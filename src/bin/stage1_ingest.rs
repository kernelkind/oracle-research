use std::env;
use std::io::{self, BufRead};
use std::thread;
use std::time::Duration;

use nostrdb::{Config, Error, Ndb};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = env::args_os()
        .nth(1)
        .ok_or("usage: stage1_ingest NDB_PATH")?;
    let path = path.to_str().ok_or("NDB path is not valid UTF-8")?;

    let no_fulltext = 1 << 2;
    let no_note_blocks = 1 << 3;
    let no_stats = 1 << 4;
    let config = Config::new()
        .set_flags(no_fulltext | no_note_blocks | no_stats)
        .set_mapsize(256 * 1024 * 1024 * 1024);
    let ndb = Ndb::new(path, &config)?;

    for line in io::stdin().lock().lines() {
        let line = line?;
        loop {
            match ndb.process_event(&line) {
                Ok(()) => break,
                Err(Error::NoteProcessFailed) => thread::sleep(Duration::from_millis(100)),
                Err(error) => return Err(error.into()),
            }
        }
    }

    thread::sleep(Duration::from_secs(60));
    drop(ndb);
    Ok(())
}
