//! Shared descriptions and integrity checks for immutable binary artifacts.

use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::snapshot::{Error, Result, io_error};

/// Description of one immutable fixed-record artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ArtifactFile {
    /// File path relative to its artifact root.
    pub file: String,
    /// Bytes in each fixed-width record.
    pub record_bytes: u32,
    /// Number of records in the file.
    pub records: u64,
    /// Total file length.
    pub bytes: u64,
    /// SHA-256 of the complete file.
    pub sha256: String,
}

pub(crate) fn describe_fixed_artifact(
    path: &Path,
    relative_path: &str,
    record_bytes: usize,
    expected_records: u64,
) -> Result<ArtifactFile> {
    let bytes = std::fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    let expected_bytes = expected_records
        .checked_mul(u64::try_from(record_bytes).expect("record width fits u64"))
        .ok_or_else(|| Error::Invariant("artifact byte length overflowed u64".to_owned()))?;
    if bytes != expected_bytes {
        return Err(Error::Invariant(format!(
            "artifact `{}` contains {bytes} bytes but expected {expected_bytes}",
            path.display()
        )));
    }
    Ok(ArtifactFile {
        file: relative_path.to_owned(),
        record_bytes: u32::try_from(record_bytes)
            .map_err(|_| Error::Invariant("record width does not fit u32".to_owned()))?,
        records: expected_records,
        bytes,
        sha256: hash_file(path)?,
    })
}

pub(crate) fn hash_file(path: &Path) -> Result<String> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let bytes = reader
            .read(&mut buffer)
            .map_err(|source| io_error("read", path, source))?;
        if bytes == 0 {
            break;
        }
        hasher.update(&buffer[..bytes]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

pub(crate) fn hash_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}
