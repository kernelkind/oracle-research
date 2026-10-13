# Worked example

Input:
```json
{
  "parent": {
    "owl": "Parent = (DisplayPanel OR (installedAsComponentIn SOME DisplayPanel))",
    "definitions": {
      "Parent": "Display panels and the components installed in them.",
      "DisplayPanel": "A device that presents visual information.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role."
    }
  },
  "nodes": [
    {
      "title": "Blue text panels",
      "meaning": "Blue text panels are display panels that show text against a uniformly blue background."
    },
    {
      "title": "Red indicator lights in blue display panels",
      "meaning": "Red indicator lights in blue display panels are lights that emit red light and are installed as components in display panels with uniformly blue backgrounds."
    }
  ]
}
```

Output:
```json
{
  "node1": {
    "owl": "BluePanel = (DisplayPanel AND (hasBackground SOME UniformlyBlueBackground))\nNode1 = (BluePanel AND (shows SOME Text))",
    "definitions": {
      "BluePanel": "A display panel with a uniformly blue background.",
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "shows": "A relation from a display panel to the visual information it presents.",
      "Text": "Written characters.",
      "Node1": "Blue text panels are display panels that show text against a uniformly blue background."
    }
  },
  "node2": {
    "owl": "BluePanel = (DisplayPanel AND (hasBackground SOME UniformlyBlueBackground))\nNode2 = (Light AND (emits SOME RedLight) AND (installedAsComponentIn SOME BluePanel))",
    "definitions": {
      "BluePanel": "A display panel with a uniformly blue background.",
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "Light": "A device that emits light.",
      "emits": "A relation from a source to light it emits.",
      "RedLight": "Light that is red.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role.",
      "Node2": "Red indicator lights in blue display panels are lights that emit red light and are installed as components in display panels with uniformly blue backgrounds."
    }
  },
  "consolidated": {
    "owl": "BluePanel = (DisplayPanel AND (hasBackground SOME UniformlyBlueBackground))\nConsolidated = (BluePanel OR (installedAsComponentIn SOME BluePanel))",
    "definitions": {
      "BluePanel": "A display panel with a uniformly blue background.",
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role.",
      "Consolidated": "Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and the components installed in them."
    }
  },
  "title": "Blue display panels",
  "meaning": "Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and the components installed in them."
}
```

The panels satisfy the first alternative of `Consolidated`; the lights satisfy the second through their installed-component role. Both alternatives fit within the supplied `Parent`. The blue condition belongs to the panels' backgrounds, not to the light emitted by their components; `SOME RedLight` does not require the lights to emit only red light.
