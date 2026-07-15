//! English-eligibility input normalization and deterministic corpus sampling.

use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::{Path, PathBuf};

use bech32::Bech32;
use bech32::primitives::decode::CheckedHrpstring;
use linkify::{LinkFinder, LinkKind};
use sha2::{Digest, Sha256};
use thiserror::Error;

const EVENT_ID_BYTES: usize = 32;
const SAMPLE_DOMAIN: &[u8] = b"oracle-mvp/english-filter-sample/v1\0";
const NIP19_PREFIXES: [&str; 7] = [
    "nprofile", "nevent", "nrelay", "naddr", "npub", "nsec", "note",
];
const MAX_NIP19_CHARACTERS: usize = 5_000;

type EventId = [u8; EVENT_ID_BYTES];

/// A deterministic English-filter preparation failure.
#[derive(Debug, Error)]
pub enum Error {
    /// Reading the ordered corpus failed.
    #[error("failed to read `{path}`: {source}")]
    Io {
        /// Input path.
        path: PathBuf,
        /// Filesystem error.
        #[source]
        source: std::io::Error,
    },

    /// The ordered corpus or sampling request violates a required invariant.
    #[error("English-filter invariant failed: {0}")]
    Invariant(String),
}

/// Build the text supplied to language identification without changing event content.
pub fn classifier_input(content: &str) -> String {
    let mut removed = url_ranges(content);
    removed.extend(nip19_ranges(content));
    removed.sort_unstable_by_key(|range| (range.start, range.end));
    let removed = merge_ranges(removed);

    let mut retained = String::with_capacity(content.len());
    let mut cursor = 0;
    for range in removed {
        retained.push_str(&content[cursor..range.start]);
        retained.push(' ');
        cursor = range.end;
    }
    retained.push_str(&content[cursor..]);

    retained
        .split_whitespace()
        .filter_map(clean_retained_token)
        .collect::<Vec<_>>()
        .join(" ")
}

/// Select an equal-probability deterministic sample from every ordered event ID.
pub fn select_sampled_event_ids(
    ordered_event_ids_path: impl AsRef<Path>,
    sample_size: usize,
    seed: &[u8],
) -> Result<Vec<EventId>, Error> {
    let path = ordered_event_ids_path.as_ref();
    if sample_size == 0 {
        return Err(Error::Invariant(
            "sample size must be greater than zero".to_owned(),
        ));
    }
    if seed.is_empty() {
        return Err(Error::Invariant("sample seed must not be empty".to_owned()));
    }

    let file = File::open(path).map_err(|source| Error::Io {
        path: path.to_owned(),
        source,
    })?;
    let length = file
        .metadata()
        .map_err(|source| Error::Io {
            path: path.to_owned(),
            source,
        })?
        .len();
    if length % EVENT_ID_BYTES as u64 != 0 {
        return Err(Error::Invariant(format!(
            "ordered event-ID file has {length} bytes; expected complete 32-byte records"
        )));
    }
    let available = usize::try_from(length / EVENT_ID_BYTES as u64)
        .map_err(|_| Error::Invariant("ordered event-ID count does not fit usize".to_owned()))?;
    if sample_size > available {
        return Err(Error::Invariant(format!(
            "requested {sample_size} samples from {available} ordered event IDs"
        )));
    }

    let mut reader = BufReader::new(file);
    let mut selected = BinaryHeap::with_capacity(sample_size);
    let mut id = [0_u8; EVENT_ID_BYTES];
    for _ in 0..available {
        reader.read_exact(&mut id).map_err(|source| Error::Io {
            path: path.to_owned(),
            source,
        })?;
        let candidate = SampledId {
            key: sample_key(seed, &id),
            id,
        };
        if selected.len() < sample_size {
            selected.push(candidate);
        } else if selected.peek().is_some_and(|largest| candidate < *largest) {
            selected.pop();
            selected.push(candidate);
        }
    }

    let mut selected = selected.into_vec();
    selected.sort_unstable();
    Ok(selected.into_iter().map(|sample| sample.id).collect())
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ByteRange {
    start: usize,
    end: usize,
}

fn url_ranges(content: &str) -> Vec<ByteRange> {
    let mut finder = LinkFinder::new();
    finder
        .kinds(&[LinkKind::Url])
        .url_must_have_scheme(false)
        .url_can_be_iri(true);
    let mut ranges = finder
        .links(content)
        .filter(|link| accepted_linkified_url(link.as_str()))
        .map(|link| ByteRange {
            start: link.start(),
            end: link.end(),
        })
        .collect::<Vec<_>>();
    for explicit in explicit_url_ranges(content) {
        let standard_web_url = standard_web_scheme_length(&content[explicit.start..]).is_some();
        if !standard_web_url
            || !ranges
                .iter()
                .any(|found| explicit.start < found.end && found.start < explicit.end)
        {
            ranges.push(explicit);
        }
    }
    ranges
}

fn explicit_url_ranges(content: &str) -> Vec<ByteRange> {
    const OPAQUE_SCHEMES: [&str; 10] = [
        "blob:",
        "data:",
        "magnet:",
        "mailto:",
        "bitcoin:",
        "lightning:",
        "lnurl:",
        "ipfs:",
        "ipns:",
        "geo:",
    ];
    let mut ranges = Vec::new();
    for (start, _) in content.char_indices() {
        if !is_left_boundary(content, start) {
            continue;
        }
        let rest = &content[start..];
        let Some(prefix_length) = hierarchical_scheme_length(rest).or_else(|| {
            OPAQUE_SCHEMES
                .iter()
                .find(|scheme| starts_with_ignore_ascii_case(rest, scheme))
                .map(|scheme| scheme.len())
        }) else {
            continue;
        };
        let Some(mut end) = content[start + prefix_length..]
            .char_indices()
            .take_while(|(_, character)| {
                !character.is_whitespace() && !matches!(character, '<' | '>' | '"' | '\'')
            })
            .map(|(offset, character)| start + prefix_length + offset + character.len_utf8())
            .last()
        else {
            continue;
        };
        while end > start + prefix_length
            && content[..end].chars().next_back().is_some_and(|character| {
                matches!(
                    character,
                    '.' | ',' | ';' | ':' | '!' | '?' | ')' | ']' | '}'
                )
            })
        {
            end -= content[..end]
                .chars()
                .next_back()
                .expect("trailing character")
                .len_utf8();
        }
        ranges.push(ByteRange { start, end });
    }
    ranges
}

fn accepted_linkified_url(candidate: &str) -> bool {
    if starts_with_ignore_ascii_case(candidate, "nostr:") {
        return false;
    }
    if hierarchical_scheme_length(candidate).is_some()
        || starts_with_ignore_ascii_case(candidate, "www.")
    {
        return true;
    }

    let authority_end = candidate.find(['/', '?', '#']).unwrap_or(candidate.len());
    let authority = &candidate[..authority_end];
    let host = authority
        .rsplit_once('@')
        .map_or(authority, |(_, host)| host);
    let host = host
        .rsplit_once(':')
        .filter(|(_, port)| !port.is_empty() && port.bytes().all(|byte| byte.is_ascii_digit()))
        .map_or(host, |(host, _)| host);
    let Some((_, top_level_domain)) = host.rsplit_once('.') else {
        return false;
    };
    let has_lowercase = top_level_domain
        .chars()
        .any(|character| character.is_lowercase());
    let has_uppercase = top_level_domain
        .chars()
        .any(|character| character.is_uppercase());
    !(has_lowercase && has_uppercase)
}

fn hierarchical_scheme_length(candidate: &str) -> Option<usize> {
    let delimiter = candidate.find("://")?;
    let scheme = &candidate[..delimiter];
    let mut characters = scheme.chars();
    if !characters
        .next()
        .is_some_and(|character| character.is_ascii_alphabetic())
        || !characters.all(|character| {
            character.is_ascii_alphanumeric() || matches!(character, '+' | '-' | '.')
        })
    {
        return None;
    }
    Some(delimiter + "://".len())
}

fn standard_web_scheme_length(candidate: &str) -> Option<usize> {
    let length = hierarchical_scheme_length(candidate)?;
    let scheme = &candidate[..length - "://".len()];
    if ["http", "https", "ws", "wss", "ftp", "ftps"]
        .iter()
        .any(|web_scheme| scheme.eq_ignore_ascii_case(web_scheme))
    {
        return Some(length);
    }
    None
}

fn nip19_ranges(content: &str) -> Vec<ByteRange> {
    let mut ranges = Vec::new();
    for (start, _) in content.char_indices() {
        if !is_left_boundary(content, start) {
            continue;
        }
        let rest = &content[start..];
        let identifier_offset = if starts_with_ignore_ascii_case(rest, "nostr:") {
            "nostr:".len()
        } else {
            0
        };
        let identifier = &rest[identifier_offset..];
        let Some(prefix) = NIP19_PREFIXES.iter().find(|prefix| {
            starts_with_ignore_ascii_case(identifier, prefix)
                && identifier.as_bytes().get(prefix.len()) == Some(&b'1')
        }) else {
            continue;
        };
        let data_start = identifier_offset + prefix.len() + 1;
        let data_length = rest[data_start..]
            .char_indices()
            .take_while(|(_, character)| is_bech32_data_character(*character))
            .map(|(_, character)| character.len_utf8())
            .sum::<usize>();
        let identifier_end = data_start + data_length;
        if identifier_end == data_start
            || identifier_end.saturating_sub(identifier_offset) > MAX_NIP19_CHARACTERS
        {
            continue;
        }
        let candidate = &rest[identifier_offset..identifier_end];
        if !valid_nip19(candidate) {
            continue;
        }

        let mut end = start + identifier_end;
        if !is_right_boundary(content, end) {
            continue;
        }
        if identifier_offset > 0 {
            end = extend_nostr_uri_suffix(content, end);
        }
        ranges.push(ByteRange { start, end });
    }
    ranges
}

fn valid_nip19(candidate: &str) -> bool {
    let Ok(decoded) = CheckedHrpstring::new::<Bech32>(candidate) else {
        return false;
    };
    let hrp = decoded.hrp().to_string().to_ascii_lowercase();
    let payload = decoded.byte_iter().collect::<Vec<_>>();
    match hrp.as_str() {
        "npub" | "nsec" | "note" => payload.len() == 32,
        "nprofile" => {
            let Ok(fields) = parse_tlv(&payload) else {
                return false;
            };
            field_count(&fields, 0) == 1
                && fields_valid(&fields, 0, |value| value.len() == 32)
                && relay_fields_valid(&fields)
                && field_count(&fields, 2) == 0
                && field_count(&fields, 3) == 0
        }
        "nevent" => {
            let Ok(fields) = parse_tlv(&payload) else {
                return false;
            };
            field_count(&fields, 0) == 1
                && fields_valid(&fields, 0, |value| value.len() == 32)
                && relay_fields_valid(&fields)
                && optional_fixed_field_valid(&fields, 2, 32)
                && optional_fixed_field_valid(&fields, 3, 4)
        }
        "naddr" => {
            let Ok(fields) = parse_tlv(&payload) else {
                return false;
            };
            field_count(&fields, 0) == 1
                && fields_valid(&fields, 0, |value| std::str::from_utf8(value).is_ok())
                && relay_fields_valid(&fields)
                && required_fixed_field_valid(&fields, 2, 32)
                && required_fixed_field_valid(&fields, 3, 4)
        }
        "nrelay" => {
            let Ok(fields) = parse_tlv(&payload) else {
                return false;
            };
            field_count(&fields, 0) == 1
                && fields_valid(&fields, 0, valid_relay_url)
                && field_count(&fields, 1) == 0
                && field_count(&fields, 2) == 0
                && field_count(&fields, 3) == 0
        }
        _ => false,
    }
}

fn field_count(fields: &[(u8, &[u8])], wanted: u8) -> usize {
    fields.iter().filter(|(kind, _)| *kind == wanted).count()
}

fn fields_valid(fields: &[(u8, &[u8])], wanted: u8, validate: impl Fn(&[u8]) -> bool) -> bool {
    fields
        .iter()
        .filter(|(kind, _)| *kind == wanted)
        .all(|(_, value)| validate(value))
}

fn relay_fields_valid(fields: &[(u8, &[u8])]) -> bool {
    fields_valid(fields, 1, valid_relay_url)
}

fn required_fixed_field_valid(fields: &[(u8, &[u8])], kind: u8, length: usize) -> bool {
    field_count(fields, kind) == 1 && fields_valid(fields, kind, |value| value.len() == length)
}

fn optional_fixed_field_valid(fields: &[(u8, &[u8])], kind: u8, length: usize) -> bool {
    field_count(fields, kind) <= 1 && fields_valid(fields, kind, |value| value.len() == length)
}

fn valid_relay_url(value: &[u8]) -> bool {
    std::str::from_utf8(value).is_ok_and(|relay| {
        let address = if starts_with_ignore_ascii_case(relay, "wss://") {
            &relay["wss://".len()..]
        } else if starts_with_ignore_ascii_case(relay, "ws://") {
            &relay["ws://".len()..]
        } else {
            return false;
        };
        !address.is_empty() && !address.chars().any(char::is_whitespace)
    })
}

fn parse_tlv(payload: &[u8]) -> Result<Vec<(u8, &[u8])>, ()> {
    let mut fields = Vec::new();
    let mut offset = 0;
    while offset < payload.len() {
        let kind = *payload.get(offset).ok_or(())?;
        let length = usize::from(*payload.get(offset + 1).ok_or(())?);
        let start = offset.checked_add(2).ok_or(())?;
        let end = start.checked_add(length).ok_or(())?;
        fields.push((kind, payload.get(start..end).ok_or(())?));
        offset = end;
    }
    Ok(fields)
}

fn is_left_boundary(content: &str, start: usize) -> bool {
    content[..start]
        .chars()
        .next_back()
        .is_none_or(|character| !character.is_alphanumeric() && character != '_')
}

fn is_right_boundary(content: &str, end: usize) -> bool {
    content[end..]
        .chars()
        .next()
        .is_none_or(|character| !character.is_alphanumeric() && character != '_')
}

fn is_bech32_data_character(character: char) -> bool {
    matches!(
        character.to_ascii_lowercase(),
        'q' | 'p'
            | 'z'
            | 'r'
            | 'y'
            | '9'
            | 'x'
            | '8'
            | 'g'
            | 'f'
            | '2'
            | 't'
            | 'v'
            | 'd'
            | 'w'
            | '0'
            | 's'
            | '3'
            | 'j'
            | 'n'
            | '5'
            | '4'
            | 'k'
            | 'h'
            | 'c'
            | 'e'
            | '6'
            | 'm'
            | 'u'
            | 'a'
            | '7'
            | 'l'
    )
}

fn extend_nostr_uri_suffix(content: &str, identifier_end: usize) -> usize {
    if !content[identifier_end..].starts_with(['?', '#']) {
        return identifier_end;
    }
    content[identifier_end..]
        .char_indices()
        .take_while(|(_, character)| {
            !character.is_whitespace() && !matches!(character, ')' | ']' | '}' | '>' | '"' | '\'')
        })
        .map(|(offset, character)| identifier_end + offset + character.len_utf8())
        .last()
        .unwrap_or(identifier_end)
}

fn merge_ranges(ranges: Vec<ByteRange>) -> Vec<ByteRange> {
    let mut merged: Vec<ByteRange> = Vec::with_capacity(ranges.len());
    for range in ranges {
        if let Some(previous) = merged.last_mut()
            && range.start <= previous.end
        {
            previous.end = previous.end.max(range.end);
        } else {
            merged.push(range);
        }
    }
    merged
}

fn clean_retained_token(token: &str) -> Option<&str> {
    let token = token.trim_matches(|character: char| {
        matches!(
            character,
            '(' | ')'
                | '['
                | ']'
                | '{'
                | '}'
                | '<'
                | '>'
                | '"'
                | '\''
                | '.'
                | ','
                | ';'
                | ':'
                | '!'
                | '?'
                | '#'
        )
    });
    (!token.is_empty()).then_some(token)
}

fn starts_with_ignore_ascii_case(value: &str, prefix: &str) -> bool {
    value
        .get(..prefix.len())
        .is_some_and(|candidate| candidate.eq_ignore_ascii_case(prefix))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SampledId {
    key: [u8; 32],
    id: EventId,
}

impl Ord for SampledId {
    fn cmp(&self, other: &Self) -> Ordering {
        self.key
            .cmp(&other.key)
            .then_with(|| self.id.cmp(&other.id))
    }
}

impl PartialOrd for SampledId {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn sample_key(seed: &[u8], id: &EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(SAMPLE_DOMAIN);
    hasher.update((seed.len() as u64).to_be_bytes());
    hasher.update(seed);
    hasher.update(id);
    hasher.finalize().into()
}
