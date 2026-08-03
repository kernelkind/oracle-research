//! Generic broad-to-narrow subject navigation.

use std::collections::{BTreeMap, BTreeSet};

use crate::reference_map::ApprovedHierarchy;
use crate::snapshot::{Error, Result};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NavigationNote {
    pub note_id: String,
    pub content: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NavigationNode {
    pub node_id: String,
    pub label: String,
    pub children: Vec<String>,
    pub note_ids: Vec<String>,
}

impl NavigationNode {
    pub fn is_leaf(&self) -> bool {
        self.children.is_empty()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NavigationHierarchy {
    pub root_node_id: String,
    pub notes: Vec<NavigationNote>,
    pub nodes: Vec<NavigationNode>,
}

impl NavigationHierarchy {
    pub fn validate(&self) -> Result<()> {
        let mut note_ids = BTreeSet::new();
        for note in &self.notes {
            if note.note_id.trim().is_empty()
                || note.content.trim().is_empty()
                || !note_ids.insert(note.note_id.as_str())
            {
                return invalid("navigation notes must be unique, valid, and nonempty");
            }
        }

        let mut nodes = BTreeMap::new();
        for node in &self.nodes {
            if node.node_id.trim().is_empty()
                || node.label.trim().is_empty()
                || nodes.insert(node.node_id.as_str(), node).is_some()
            {
                return invalid("navigation hierarchy contains an invalid or duplicate node");
            }
            if node.is_leaf() {
                if node.note_ids.is_empty() {
                    return invalid(format!("leaf {} contains no notes", node.node_id));
                }
            } else if !(2..=8).contains(&node.children.len()) || !node.note_ids.is_empty() {
                return invalid(format!(
                    "internal node {} must have 2 through at most 8 children and no direct notes",
                    node.node_id
                ));
            }
        }

        let root = nodes.get(self.root_node_id.as_str()).ok_or_else(|| {
            Error::ExperimentState("navigation hidden root is missing".to_owned())
        })?;
        if root.is_leaf() {
            return invalid("navigation hidden root must be internal");
        }

        let mut parent_counts = BTreeMap::<&str, usize>::new();
        for node in &self.nodes {
            let unique_children = node.children.iter().collect::<BTreeSet<_>>();
            if unique_children.len() != node.children.len() {
                return invalid(format!("node {} repeats a child", node.node_id));
            }
            for child in &node.children {
                if !nodes.contains_key(child.as_str()) {
                    return invalid(format!("node {} names missing child {child}", node.node_id));
                }
                *parent_counts.entry(child.as_str()).or_default() += 1;
            }
        }
        for node in &self.nodes {
            let parents = parent_counts
                .get(node.node_id.as_str())
                .copied()
                .unwrap_or(0);
            if (node.node_id == self.root_node_id && parents != 0)
                || (node.node_id != self.root_node_id && parents != 1)
            {
                return invalid(format!(
                    "node {} does not have the required parent count",
                    node.node_id
                ));
            }
        }

        let mut visiting = BTreeSet::new();
        let mut visited = BTreeSet::new();
        visit_node(
            self.root_node_id.as_str(),
            &nodes,
            &mut visiting,
            &mut visited,
        )?;
        if visited.len() != nodes.len() {
            return invalid("every navigation node must be reachable");
        }

        let mut covered = BTreeSet::new();
        for leaf in self.nodes.iter().filter(|node| node.is_leaf()) {
            let mut local = BTreeSet::new();
            for note_id in &leaf.note_ids {
                if !note_ids.contains(note_id.as_str()) || !local.insert(note_id.as_str()) {
                    return invalid(format!(
                        "leaf {} contains an invalid or duplicate note",
                        leaf.node_id
                    ));
                }
                covered.insert(note_id.as_str());
            }
        }
        if covered != note_ids {
            return invalid("every navigation note must belong to at least one leaf");
        }
        Ok(())
    }

    pub fn node(&self, node_id: &str) -> Option<&NavigationNode> {
        self.nodes.iter().find(|node| node.node_id == node_id)
    }

    pub fn leaf_notes(&self, node_id: &str) -> Result<Vec<&NavigationNote>> {
        self.validate()?;
        let node = self
            .node(node_id)
            .ok_or_else(|| Error::ExperimentState(format!("subject node {node_id} is missing")))?;
        if !node.is_leaf() {
            return invalid(format!("subject node {node_id} is not a leaf"));
        }
        let notes = self
            .notes
            .iter()
            .map(|note| (note.note_id.as_str(), note))
            .collect::<BTreeMap<_, _>>();
        Ok(node
            .note_ids
            .iter()
            .map(|note_id| notes[note_id.as_str()])
            .collect())
    }
}

impl TryFrom<&ApprovedHierarchy> for NavigationHierarchy {
    type Error = Error;

    fn try_from(approved: &ApprovedHierarchy) -> Result<Self> {
        approved.validate()?;
        let notes = approved
            .notes
            .iter()
            .map(|note| NavigationNote {
                note_id: note.note_id.clone(),
                content: note.content.clone(),
            })
            .collect();
        let nodes = approved
            .nodes
            .iter()
            .map(|node| {
                let note_ids = if node.is_leaf() {
                    approved
                        .leaf_notes(&node.node_id)?
                        .into_iter()
                        .map(|note| note.note_id.clone())
                        .collect()
                } else {
                    Vec::new()
                };
                Ok(NavigationNode {
                    node_id: node.node_id.clone(),
                    label: node.label.clone(),
                    children: node.children.clone(),
                    note_ids,
                })
            })
            .collect::<Result<Vec<_>>>()?;
        let hierarchy = Self {
            root_node_id: approved.root_node_id.clone(),
            notes,
            nodes,
        };
        hierarchy.validate()?;
        Ok(hierarchy)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct NavigationFrame {
    node_id: String,
    cursor: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SubjectNavigation {
    frames: Vec<NavigationFrame>,
}

impl SubjectNavigation {
    pub fn new(hierarchy: &NavigationHierarchy) -> Result<Self> {
        hierarchy.validate()?;
        Ok(Self {
            frames: vec![NavigationFrame {
                node_id: hierarchy.root_node_id.clone(),
                cursor: 0,
            }],
        })
    }

    pub fn current_node_id(&self) -> &str {
        &self
            .frames
            .last()
            .expect("navigation always contains its hidden root")
            .node_id
    }

    pub fn selected_index(&self) -> usize {
        self.frames
            .last()
            .expect("navigation always contains its hidden root")
            .cursor
    }

    pub fn move_next(&mut self, hierarchy: &NavigationHierarchy) {
        let count = self.current_item_count(hierarchy);
        if count == 0 {
            return;
        }
        let frame = self
            .frames
            .last_mut()
            .expect("navigation always contains its hidden root");
        frame.cursor = (frame.cursor + 1).min(count - 1);
    }

    pub fn move_previous(&mut self) {
        let frame = self
            .frames
            .last_mut()
            .expect("navigation always contains its hidden root");
        frame.cursor = frame.cursor.saturating_sub(1);
    }

    pub fn enter(&mut self, hierarchy: &NavigationHierarchy) -> Result<()> {
        hierarchy.validate()?;
        let node = hierarchy.node(self.current_node_id()).ok_or_else(|| {
            Error::ExperimentState(format!(
                "current subject node {} is missing",
                self.current_node_id()
            ))
        })?;
        if node.is_leaf() {
            return Ok(());
        }
        let child = node
            .children
            .get(self.selected_index())
            .ok_or_else(|| Error::ExperimentState("subject cursor is invalid".to_owned()))?;
        self.frames.push(NavigationFrame {
            node_id: child.clone(),
            cursor: 0,
        });
        Ok(())
    }

    pub fn back(&mut self) {
        if self.frames.len() > 1 {
            self.frames.pop();
        }
    }

    pub fn breadcrumb<'a>(&self, hierarchy: &'a NavigationHierarchy) -> Result<Vec<&'a str>> {
        self.frames
            .iter()
            .skip(1)
            .map(|frame| {
                hierarchy
                    .node(&frame.node_id)
                    .map(|node| node.label.as_str())
                    .ok_or_else(|| {
                        Error::ExperimentState(format!(
                            "breadcrumb subject {} is missing",
                            frame.node_id
                        ))
                    })
            })
            .collect()
    }

    pub fn selected_note<'a>(
        &self,
        hierarchy: &'a NavigationHierarchy,
    ) -> Result<Option<&'a NavigationNote>> {
        let node = hierarchy.node(self.current_node_id()).ok_or_else(|| {
            Error::ExperimentState(format!(
                "current subject node {} is missing",
                self.current_node_id()
            ))
        })?;
        if !node.is_leaf() {
            return Ok(None);
        }
        Ok(hierarchy
            .leaf_notes(&node.node_id)?
            .get(self.selected_index())
            .copied())
    }

    fn current_item_count(&self, hierarchy: &NavigationHierarchy) -> usize {
        let Some(node) = hierarchy.node(self.current_node_id()) else {
            return 0;
        };
        if node.is_leaf() {
            node.note_ids.len()
        } else {
            node.children.len()
        }
    }
}

fn visit_node<'a>(
    node_id: &'a str,
    nodes: &BTreeMap<&'a str, &'a NavigationNode>,
    visiting: &mut BTreeSet<&'a str>,
    visited: &mut BTreeSet<&'a str>,
) -> Result<()> {
    if visited.contains(node_id) {
        return Ok(());
    }
    if !visiting.insert(node_id) {
        return invalid(format!(
            "navigation hierarchy contains a cycle at node {node_id}"
        ));
    }
    let node = nodes
        .get(node_id)
        .ok_or_else(|| Error::ExperimentState(format!("navigation node {node_id} is missing")))?;
    for child in &node.children {
        visit_node(child, nodes, visiting, visited)?;
    }
    visiting.remove(node_id);
    visited.insert(node_id);
    Ok(())
}

fn invalid<T>(message: impl Into<String>) -> Result<T> {
    Err(Error::ExperimentState(message.into()))
}
