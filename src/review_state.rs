//! Shared durable storage for human review sessions and approved artifacts.

use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Read, Write};
use std::path::Path;

use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::snapshot::{Error, Result, io_error};

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SessionEnvelope<T> {
    schema_version: u32,
    state_sha256: String,
    session: T,
}

pub(crate) fn load_session<T>(path: &Path) -> Result<Option<T>>
where
    T: DeserializeOwned + Serialize,
{
    if !path.exists() {
        return Ok(None);
    }
    let envelope: SessionEnvelope<T> = load_json(path)?;
    if envelope.schema_version != 1 {
        return Err(Error::ExperimentState(format!(
            "review session `{}` has an unsupported schema",
            path.display()
        )));
    }
    let expected = value_sha256(&envelope.session)?;
    if envelope.state_sha256 != expected {
        return Err(Error::ExperimentState(format!(
            "review session `{}` failed its state hash",
            path.display()
        )));
    }
    Ok(Some(envelope.session))
}

pub(crate) fn save_session<T: Serialize>(path: &Path, session: &T) -> Result<()> {
    let envelope = SessionEnvelope {
        schema_version: 1,
        state_sha256: value_sha256(session)?,
        session,
    };
    replace_json(path, &envelope)
}

pub(crate) fn publish_session<T: Serialize>(path: &Path, session: &T) -> Result<()> {
    let envelope = SessionEnvelope {
        schema_version: 1,
        state_sha256: value_sha256(session)?,
        session,
    };
    write_json_atomic(path, &envelope, false)
}

pub(crate) fn load_json<T: DeserializeOwned>(path: &Path) -> Result<T> {
    let mut bytes = Vec::new();
    File::open(path)
        .and_then(|mut file| file.read_to_end(&mut bytes))
        .map_err(|source| io_error("read", path, source))?;
    serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })
}

pub(crate) fn value_sha256<T: Serialize>(value: &T) -> Result<String> {
    let bytes = serde_json::to_vec(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: "<review-state-identity>".into(),
        source,
    })?;
    Ok(format!("{:x}", Sha256::digest(bytes)))
}

pub(crate) fn publish_json<T>(path: &Path, value: &T) -> Result<()>
where
    T: DeserializeOwned + Serialize + PartialEq,
{
    if path.exists() {
        let existing: T = load_json(path)?;
        if &existing == value {
            return Ok(());
        }
        return Err(Error::ArtifactExists(path.to_owned()));
    }
    write_json_atomic(path, value, false)
}

pub(crate) fn replace_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    write_json_atomic(path, value, true)
}

fn write_json_atomic<T: Serialize>(path: &Path, value: &T, replace: bool) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    prepare_directory(parent)?;
    if !replace && path.exists() {
        return Err(Error::ArtifactExists(path.to_owned()));
    }
    let filename = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = parent.join(format!(".{filename}.{}.tmp", std::process::id()));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    let mut options = OpenOptions::new();
    options.create_new(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    let mut writer = BufWriter::new(file);
    let result = (|| {
        serde_json::to_writer_pretty(&mut writer, value).map_err(|source| Error::Manifest {
            operation: "encode",
            path: temporary.clone(),
            source,
        })?;
        writer
            .write_all(b"\n")
            .and_then(|()| writer.flush())
            .map_err(|source| io_error("write", &temporary, source))?;
        writer
            .get_ref()
            .sync_all()
            .map_err(|source| io_error("sync", &temporary, source))?;
        if replace {
            fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
        } else {
            match fs::hard_link(&temporary, path) {
                Ok(()) => {
                    fs::remove_file(&temporary)
                        .map_err(|source| io_error("remove", &temporary, source))?;
                }
                Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
                    return Err(Error::ArtifactExists(path.to_owned()));
                }
                Err(source) => return Err(io_error("publish", path, source)),
            }
        }
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", parent, source))
    })();
    if result.is_err() && temporary.exists() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

fn prepare_directory(path: &Path) -> Result<()> {
    let mut builder = fs::DirBuilder::new();
    builder.recursive(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::DirBuilderExt as _;
        builder.mode(0o700);
    }
    builder
        .create(path)
        .map_err(|source| io_error("create", path, source))
}

pub(crate) fn acquire_session_lock(session_path: &Path) -> Result<File> {
    let parent = session_path.parent().unwrap_or_else(|| Path::new("."));
    prepare_directory(parent)?;
    let filename = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    let lock_path = parent.join(format!(".{filename}.lock"));
    let mut options = OpenOptions::new();
    options.create(true).read(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(&lock_path)
        .map_err(|source| io_error("open", &lock_path, source))?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "review session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &lock_path, source)),
    }
}
