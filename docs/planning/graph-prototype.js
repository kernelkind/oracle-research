(() => {
  'use strict';

  const statusElement = document.getElementById('graph-status');
  const detailsElement = document.getElementById('details');
  const taskSelect = document.getElementById('focus-task');
  const depthSelect = document.getElementById('depth');
  const directionSelect = document.getElementById('direction');
  const inputsCheckbox = document.getElementById('show-inputs');
  const backButton = document.getElementById('go-back');
  const showAllButton = document.getElementById('show-all');
  const focusButton = document.getElementById('focus-selected');

  let tasks;
  let links;
  let graph;
  let layout;
  let focusId;
  let allMode = false;
  const history = [];

  const statusKeys = {
    COMPLETE: 'complete',
    'IN PROGRESS': 'active',
    'READY TO START': 'ready',
    'READY TO RESUME': 'ready',
    PAUSED: 'paused',
    'VALIDATION PENDING': 'waiting',
    WAITING: 'waiting',
  };

  function readPlan(data) {
    if (!data || !Array.isArray(data.tasks) || !Array.isArray(data.links)) {
      throw new Error('The task file needs tasks and links arrays');
    }
    const foundTasks = new Map();
    for (const task of data.tasks) {
      if (!task || typeof task.id !== 'string' || !/^\d{2}$/.test(task.id) ||
        typeof task.title !== 'string' || !task.title.trim() ||
        typeof task.description !== 'string' || !Object.hasOwn(statusKeys, task.status) ||
        foundTasks.has(task.id)) {
        throw new Error(`Invalid or duplicate task ${task?.id ?? '(missing ID)'}`);
      }
      foundTasks.set(task.id, {...task, statusKey: statusKeys[task.status]});
    }
    if (!foundTasks.size) throw new Error('No tasks found in the task file');
    const seenLinks = new Set();
    const foundLinks = data.links.map(link => {
      const id = `${link?.source}-${link?.target}-${link?.kind}`;
      if (!link || !foundTasks.has(link.source) || !foundTasks.has(link.target) ||
        link.source === link.target || !['required', 'helpful'].includes(link.kind) ||
        (link.label !== undefined && typeof link.label !== 'string') || seenLinks.has(id)) {
        throw new Error(`Invalid or duplicate link ${id}`);
      }
      seenLinks.add(id);
      return {...link, id, label: link.label || '', helpful: link.kind === 'helpful'};
    });
    if (!foundLinks.length) throw new Error('No task dependencies found in the plan');
    return {tasks: foundTasks, links: foundLinks};
  }

  function sortedTasks() {
    return [...tasks.values()].sort((a, b) =>
      Number(a.id) - Number(b.id) || a.title.localeCompare(b.title));
  }

  function displayName(id) {
    const task = tasks.get(id);
    return `${task.id} · ${task.title}`;
  }

  function visibleTaskIds() {
    if (allMode) return new Set(tasks.keys());
    const visible = new Set([focusId]);
    let frontier = new Set([focusId]);
    const depth = Number(depthSelect.value);
    const direction = directionSelect.value;
    for (let step = 0; step < depth; step++) {
      const next = new Set();
      for (const link of links) {
        if (link.helpful && !inputsCheckbox.checked) continue;
        if (direction !== 'after' && frontier.has(link.target) && !visible.has(link.source)) {
          next.add(link.source);
        }
        if (direction !== 'before' && frontier.has(link.source) && !visible.has(link.target)) {
          next.add(link.target);
        }
      }
      next.forEach(id => visible.add(id));
      frontier = next;
    }
    return visible;
  }

  function appendRelatedSection(heading, relatedLinks, otherEnd) {
    const sectionHeading = document.createElement('h3');
    sectionHeading.textContent = heading;
    detailsElement.append(sectionHeading);
    if (!relatedLinks.length) {
      const empty = document.createElement('p');
      empty.className = 'muted';
      empty.textContent = 'None recorded.';
      detailsElement.append(empty);
      return;
    }
    const list = document.createElement('div');
    list.className = 'related';
    relatedLinks.sort((a, b) => Number(a[otherEnd]) - Number(b[otherEnd]));
    for (const link of relatedLinks) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = displayName(link[otherEnd]);
      if (link.label) {
        const label = document.createElement('small');
        label.textContent = link.label;
        button.append(label);
      }
      button.addEventListener('click', () => chooseFocus(link[otherEnd]));
      list.append(button);
    }
    detailsElement.append(list);
  }

  function updateDetails() {
    const task = tasks.get(focusId);
    detailsElement.replaceChildren();
    const heading = document.createElement('h2');
    heading.textContent = displayName(task.id);
    detailsElement.append(heading);
    const status = document.createElement('span');
    status.className = `task-status ${task.statusKey}`;
    status.textContent = task.status;
    detailsElement.append(status);
    if (task.description) {
      const description = document.createElement('p');
      description.className = 'description';
      description.textContent = task.description;
      detailsElement.append(description);
    }
    const incoming = links.filter(link => link.target === task.id);
    const outgoing = links.filter(link => link.source === task.id);
    appendRelatedSection('Needed to finish', incoming.filter(link => !link.helpful), 'source');
    appendRelatedSection('Helpful inputs', incoming.filter(link => link.helpful), 'source');
    appendRelatedSection('Unlocks', outgoing.filter(link => !link.helpful), 'target');
    appendRelatedSection('Informs', outgoing.filter(link => link.helpful), 'target');
    const legend = document.createElement('div');
    legend.className = 'legend';
    const explanation = document.createElement('p');
    explanation.textContent = 'Solid arrows are prerequisites to finish the next task. Dashed arrows are helpful inputs. A task may be able to start earlier; check its description. “Other links” on a card means some of its arrows are not drawn in this view.';
    legend.append(explanation);
    detailsElement.append(legend);
  }

  function render() {
    if (layout) layout.stop();
    const visible = visibleTaskIds();
    const visibleLinks = new Set(links.filter(link => visible.has(link.source) &&
      visible.has(link.target) && (!link.helpful || inputsCheckbox.checked))
      .map(link => link.id));
    const hiddenByTask = new Map([...tasks.keys()].map(id => [id, 0]));
    for (const link of links) {
      if (visibleLinks.has(link.id)) continue;
      if (visible.has(link.source)) hiddenByTask.set(link.source, hiddenByTask.get(link.source) + 1);
      if (visible.has(link.target)) hiddenByTask.set(link.target, hiddenByTask.get(link.target) + 1);
    }
    graph.batch(() => {
      graph.nodes().forEach(node => {
        const task = tasks.get(node.id());
        const hidden = hiddenByTask.get(node.id());
        node.data('label', `${task.id} · ${task.title}${hidden ? `\n+${hidden} other links` : ''}`);
        node.toggleClass('hidden', !visible.has(node.id()));
        node.toggleClass('focused', node.id() === focusId);
      });
      graph.edges().forEach(edge => edge.toggleClass('hidden', !visibleLinks.has(edge.id())));
    });
    const hiddenLinks = links.length - visibleLinks.size;
    statusElement.textContent = `Showing ${visible.size} of ${tasks.size} tasks · ${hiddenLinks} other links hidden. Click a task to focus; scroll to zoom, drag to pan.`;
    taskSelect.value = focusId;
    depthSelect.disabled = allMode;
    directionSelect.disabled = allMode;
    showAllButton.disabled = allMode;
    backButton.disabled = history.length === 0;
    focusButton.disabled = !allMode;
    updateDetails();
    layout = graph.elements(':visible').layout({
      name: 'elk',
      fit: true,
      padding: 35,
      animate: false,
      nodeDimensionsIncludeLabels: true,
      elk: {
        algorithm: 'layered',
        'elk.direction': 'RIGHT',
        'elk.spacing.nodeNode': '42',
        'elk.layered.spacing.nodeNodeBetweenLayers': '95',
      },
    });
    layout.run();
  }

  function chooseFocus(id) {
    if (!tasks.has(id)) return;
    if (id !== focusId) history.push(focusId);
    focusId = id;
    allMode = false;
    render();
  }

  function createGraph() {
    const elements = [
      ...sortedTasks().map(task => ({
        data: {id: task.id, label: displayName(task.id)},
        classes: task.statusKey,
      })),
      ...links.map(link => ({
        data: {id: link.id, source: link.source, target: link.target},
        classes: link.helpful ? 'helpful' : 'required',
      })),
    ];
    graph = cytoscape({
      container: document.getElementById('graph'),
      elements,
      layout: {name: 'preset'},
      autoungrabify: true,
      minZoom: 0.25,
      maxZoom: 2.5,
      wheelSensitivity: 0.17,
      style: [
        {selector: 'node', style: {
          shape: 'round-rectangle', width: 205, height: 78,
          'background-color': '#2c3a49', 'border-color': '#8da3b8',
          'border-width': 2, color: '#f0f5fa', 'font-size': 12,
          'font-weight': 600, label: 'data(label)', 'text-wrap': 'wrap',
          'text-max-width': 184, 'text-valign': 'center', 'text-halign': 'center',
          'text-margin-x': 4, 'text-margin-y': 1,
        }},
        {selector: 'node.ready', style: {'border-color': '#68d391'}},
        {selector: 'node.active', style: {'border-color': '#79b8ff'}},
        {selector: 'node.paused', style: {'border-color': '#d9ad71'}},
        {selector: 'node.complete', style: {
          'background-color': '#222d38', 'border-color': '#657589', color: '#b5c2ce',
        }},
        {selector: 'node.focused', style: {'border-width': 4, 'border-color': '#f1d08b'}},
        {selector: 'edge', style: {
          width: 2, 'line-color': '#9fb1c4', 'target-arrow-color': '#9fb1c4',
          'target-arrow-shape': 'triangle', 'curve-style': 'taxi',
          'taxi-direction': 'horizontal', 'taxi-turn': '50%',
        }},
        {selector: 'edge.helpful', style: {
          'line-style': 'dashed', 'line-color': '#c1a9df',
          'target-arrow-color': '#c1a9df',
        }},
        {selector: '.hidden', style: {display: 'none'}},
      ],
    });
    graph.on('tap', 'node', event => chooseFocus(event.target.id()));
    window.addEventListener('resize', () => graph.resize());
  }

  async function start() {
    try {
      if (typeof cytoscape !== 'function' || typeof ELK !== 'function' ||
        typeof cytoscapeElk !== 'function') {
        throw new Error('Graph libraries did not load');
      }
      if (!cytoscape('layout', 'elk')) cytoscape.use(cytoscapeElk);
      const response = await fetch('release-plan.json', {cache: 'no-store'});
      if (!response.ok) throw new Error(`The task file returned HTTP ${response.status}`);
      ({tasks, links} = readPlan(await response.json()));
      for (const task of sortedTasks()) {
        const option = document.createElement('option');
        option.value = task.id;
        option.textContent = displayName(task.id);
        taskSelect.append(option);
      }
      focusId = tasks.has('02') ? '02' : sortedTasks()[0].id;
      createGraph();
      taskSelect.addEventListener('change', () => chooseFocus(taskSelect.value));
      depthSelect.addEventListener('change', () => { allMode = false; render(); });
      directionSelect.addEventListener('change', () => { allMode = false; render(); });
      inputsCheckbox.addEventListener('change', render);
      showAllButton.addEventListener('click', () => { allMode = true; render(); });
      focusButton.addEventListener('click', () => { allMode = false; render(); });
      backButton.addEventListener('click', () => {
        if (!history.length) return;
        focusId = history.pop();
        allMode = false;
        render();
      });
      render();
    } catch (error) {
      statusElement.setAttribute('role', 'alert');
      statusElement.textContent = `Could not load graph: ${error.message}`;
    }
  }

  start();
})();
