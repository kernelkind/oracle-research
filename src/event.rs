//! Canonical representation of Nostr event IDs at oracle boundaries.

use std::fmt;
use std::str::FromStr;

use serde::{Deserialize, Deserializer, Serialize, Serializer};

const EVENT_ID_BYTES: usize = 32;
const EVENT_ID_HEX_CHARS: usize = EVENT_ID_BYTES * 2;

/// A 32-byte Nostr event ID serialized as conventional lowercase hex.
#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct EventId([u8; EVENT_ID_BYTES]);

impl EventId {
    /// Return the raw event-ID bytes.
    pub const fn as_bytes(&self) -> &[u8; EVENT_ID_BYTES] {
        &self.0
    }

    /// Consume the value and return its raw bytes.
    pub const fn into_bytes(self) -> [u8; EVENT_ID_BYTES] {
        self.0
    }
}

impl From<[u8; EVENT_ID_BYTES]> for EventId {
    fn from(value: [u8; EVENT_ID_BYTES]) -> Self {
        Self(value)
    }
}

impl From<EventId> for [u8; EVENT_ID_BYTES] {
    fn from(value: EventId) -> Self {
        value.0
    }
}

impl fmt::Display for EventId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        for byte in self.0 {
            write!(formatter, "{byte:02x}")?;
        }
        Ok(())
    }
}

impl fmt::Debug for EventId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "EventId({self})")
    }
}

impl FromStr for EventId {
    type Err = EventIdParseError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        if value.len() != EVENT_ID_HEX_CHARS {
            return Err(EventIdParseError(format!(
                "event ID contains {} hexadecimal characters; expected {EVENT_ID_HEX_CHARS}",
                value.len()
            )));
        }
        let mut bytes = [0_u8; EVENT_ID_BYTES];
        for (index, output) in bytes.iter_mut().enumerate() {
            let high = decode_nibble(value.as_bytes()[index * 2])?;
            let low = decode_nibble(value.as_bytes()[index * 2 + 1])?;
            *output = high << 4 | low;
        }
        Ok(Self(bytes))
    }
}

impl Serialize for EventId {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

impl<'de> Deserialize<'de> for EventId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        value.parse().map_err(serde::de::Error::custom)
    }
}

/// A malformed hexadecimal Nostr event ID.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EventIdParseError(String);

impl fmt::Display for EventIdParseError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl std::error::Error for EventIdParseError {}

fn decode_nibble(byte: u8) -> Result<u8, EventIdParseError> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        b'A'..=b'F' => Ok(byte - b'A' + 10),
        _ => Err(EventIdParseError(format!(
            "event ID contains non-hexadecimal byte 0x{byte:02x}"
        ))),
    }
}
