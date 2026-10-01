(() => {
  'use strict';

  const statusElement = document.getElementById('graph-status');
  const detailsElement = document.getElementById('details');
  const taskSelect = document.getElementById('focus-task');
  const trackSelect = document.getElementById('track');
  const depthSelect = document.getElementById('depth');
  const directionSelect = document.getElementById('direction');
  const inputsCheckbox = document.getElementById('show-inputs');
  const backButton = document.getElementById('go-back');
  const showAllButton = document.getElementById('show-all');
  const focusButton = document.getElementById('focus-selected');

  let tasks;
  let links;
  let graph;
  let elk;
  let renderGeneration = 0;
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

  const trackLabels = {
    release: 'Required release',
    model: 'Optional model',
    shared: 'Shared',
    historical: 'Historical experiment',
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
      if (!Object.hasOwn(trackLabels, task.track)) {
        throw new Error(`Invalid task track for ${task.id}`);
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

  function matchesTrack(task) {
    return trackSelect.value === 'both' || task.track === 'shared' ||
      task.track === trackSelect.value;
  }

  function updateTaskSelect() {
    const eligible = sortedTasks().filter(matchesTrack);
    if (!eligible.some(task => task.id === focusId)) focusId = eligible[0]?.id;
    taskSelect.replaceChildren(...eligible.map(task => {
      const option = document.createElement('option');
      option.value = task.id;
      option.textContent = displayName(task.id);
      return option;
    }));
    taskSelect.value = focusId || '';
  }

  function visibleTaskIds() {
    if (!focusId) return new Set();
    const available = id => matchesTrack(tasks.get(id));
    if (allMode) return new Set([...tasks.keys()].filter(available));
    const visible = new Set([focusId]);
    let frontier = new Set([focusId]);
    const depth = Number(depthSelect.value);
    const direction = directionSelect.value;
    for (let step = 0; step < depth; step++) {
      const next = new Set();
      for (const link of links) {
        if (link.helpful && !inputsCheckbox.checked) continue;
        if (direction !== 'after' && frontier.has(link.target) &&
          available(link.source) && !visible.has(link.source)) {
          next.add(link.source);
        }
        if (direction !== 'before' && frontier.has(link.source) &&
          available(link.target) && !visible.has(link.target)) {
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
      const relatedTask = tasks.get(link[otherEnd]);
      const annotations = [link.label];
      if (!matchesTrack(relatedTask)) {
        annotations.push(`${trackLabels[relatedTask.track]} · outside this view`);
      }
      if (annotations.some(Boolean)) {
        const label = document.createElement('small');
        label.textContent = annotations.filter(Boolean).join(' · ');
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
    if (!task) {
      const empty = document.createElement('p');
      empty.textContent = 'No tasks in this track.';
      detailsElement.append(empty);
      return;
    }
    const heading = document.createElement('h2');
    heading.textContent = displayName(task.id);
    detailsElement.append(heading);
    const status = document.createElement('span');
    status.className = `task-status ${task.statusKey}`;
    status.textContent = task.status;
    detailsElement.append(status);
    const track = document.createElement('p');
    track.className = 'task-track';
    track.textContent = task.track === 'shared' ? 'Shared · required release and optional model' : trackLabels[task.track];
    detailsElement.append(track);
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
    const generation = ++renderGeneration;
    updateTaskSelect();
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
        node.data('label', `${task.id} · ${task.title}\n${trackLabels[task.track]}${hidden ? `\n+${hidden} other links` : ''}`);
        node.toggleClass('hidden', !visible.has(node.id()));
        node.toggleClass('focused', node.id() === focusId);
      });
      graph.edges().forEach(edge => edge.toggleClass('hidden', !visibleLinks.has(edge.id())));
    });
    const hiddenLinks = links.length - visibleLinks.size;
    const viewLabel = trackSelect.value === 'both' ? 'Both tracks' : trackLabels[trackSelect.value];
    const summary = `${viewLabel} · Showing ${visible.size} of ${tasks.size} tasks · ${hiddenLinks} other links hidden.`;
    statusElement.textContent = `${summary} Arranging layout…`;
    taskSelect.value = focusId;
    depthSelect.disabled = allMode;
    directionSelect.disabled = allMode;
    showAllButton.disabled = allMode;
    backButton.disabled = history.length === 0;
    focusButton.disabled = !allMode;
    updateDetails();
    if (!visible.size) {
      statusElement.textContent = `${summary} No tasks in this track.`;
      return;
    }
    const model = {
      id: 'release-plan',
      layoutOptions: {
        'elk.algorithm': 'layered',
        'elk.direction': 'RIGHT',
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.spacing.nodeNode': '42',
        'elk.layered.spacing.nodeNodeBetweenLayers': '95',
      },
      children: sortedTasks().filter(task => visible.has(task.id)).map(task => {
        const node = graph.getElementById(task.id);
        return {id: task.id, width: node.outerWidth(), height: node.outerHeight()};
      }),
      edges: links.filter(link => visibleLinks.has(link.id)).map(link => ({
        id: link.id, sources: [link.source], targets: [link.target],
      })),
    };
    elk.layout(model).then(result => {
      if (generation !== renderGeneration) return;
      const positions = new Map(result.children.map(node => [node.id, {
        x: node.x + node.width / 2,
        y: node.y + node.height / 2,
      }]));
      graph.batch(() => {
        graph.nodes().forEach(node => {
          if (positions.has(node.id())) node.position(positions.get(node.id()));
        });
        for (const route of result.edges) {
          const edge = graph.getElementById(route.id);
          const {startPoint: start, endPoint: end, bendPoints: bends = []} = route.sections[0];
          const source = positions.get(edge.source().id());
          const target = positions.get(edge.target().id());
          const dx = end.x - start.x;
          const dy = end.y - start.y;
          const lengthSquared = dx * dx + dy * dy;
          const length = Math.sqrt(lengthSquared);
          // Cytoscape expresses bends relative to the line between endpoints.
          // Convert ELK's absolute points without changing its routing.
          const style = {
            'curve-style': bends.length ? 'segments' : 'straight',
            'source-endpoint': [start.x - source.x, start.y - source.y],
            'target-endpoint': [end.x - target.x, end.y - target.y],
          };
          if (bends.length) {
            style['segment-weights'] = bends.map(point =>
              ((point.x - start.x) * dx + (point.y - start.y) * dy) / lengthSquared);
            style['segment-distances'] = bends.map(point =>
              ((point.y - start.y) * dx - (point.x - start.x) * dy) / length);
          }
          edge.style(style);
        }
      });
      graph.fit(graph.elements(':visible'), 35);
      statusElement.textContent = `${summary} Layout ready. Click a task to focus; scroll to zoom, drag to pan.`;
    }).catch(error => {
      if (generation !== renderGeneration) return;
      statusElement.setAttribute('role', 'alert');
      statusElement.textContent = `Could not arrange graph: ${error.message}`;
    });
  }

  function chooseFocus(id) {
    if (!tasks.has(id)) return;
    if (focusId && id !== focusId) history.push({id: focusId, track: trackSelect.value});
    focusId = id;
    const task = tasks.get(id);
    if (!matchesTrack(task)) trackSelect.value = task.track === 'historical' ? 'both' : task.track;
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
          shape: 'round-rectangle', width: 205, height: 94,
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
          'target-arrow-shape': 'triangle', 'curve-style': 'straight',
          'edge-distances': 'endpoints',
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
      if (typeof cytoscape !== 'function' || typeof ELK !== 'function') {
        throw new Error('Graph libraries did not load');
      }
      elk = new ELK();
      const response = await fetch('release-plan.json', {cache: 'no-store'});
      if (!response.ok) throw new Error(`The task file returned HTTP ${response.status}`);
      ({tasks, links} = readPlan(await response.json()));
      focusId = tasks.has('02') ? '02' : sortedTasks()[0].id;
      createGraph();
      trackSelect.addEventListener('change', render);
      taskSelect.addEventListener('change', () => chooseFocus(taskSelect.value));
      depthSelect.addEventListener('change', () => { allMode = false; render(); });
      directionSelect.addEventListener('change', () => { allMode = false; render(); });
      inputsCheckbox.addEventListener('change', render);
      showAllButton.addEventListener('click', () => { allMode = true; render(); });
      focusButton.addEventListener('click', () => { allMode = false; render(); });
      backButton.addEventListener('click', () => {
        if (!history.length) return;
        const previous = history.pop();
        focusId = previous.id;
        trackSelect.value = previous.track;
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
