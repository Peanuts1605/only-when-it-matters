const timeline = document.querySelector('#timeline');
const replay = document.querySelector('#replay');

const label = {
  IGNORE: 'LET PASS',
  RECORD: 'RECORD QUIETLY',
  ESCALATE: 'HUMAN NEEDED',
};

const render = async () => {
  const response = await fetch('/report.json', { cache: 'no-store' });
  const report = await response.json();
  document.querySelector('#events').textContent = report.metrics.unique_events;
  document.querySelector('#avoided').textContent = report.metrics.interruptions_avoided;
  document.querySelector('#interruptions').textContent = report.metrics.human_interruptions;
  timeline.replaceChildren();

  report.outcomes.forEach((event, index) => {
    const row = document.createElement('article');
    row.className = `event ${event.duplicate ? 'duplicate' : ''}`;
    row.style.animationDelay = `${index * 110}ms`;
    row.innerHTML = `
      <span class="event-index">${String(index + 1).padStart(2, '0')}</span>
      <div class="event-copy"><strong>${event.contest}</strong><span>${event.event_id}${event.duplicate ? ' · duplicate replay' : ''}</span></div>
      <p class="event-reason">${event.reason}</p>
      <span class="pill ${event.decision.toLowerCase()}">${label[event.decision]}</span>
    `;
    timeline.append(row);
  });
};

replay.addEventListener('click', render);
render().catch(() => {
  timeline.textContent = 'The public proof could not be loaded. Please retry.';
});

