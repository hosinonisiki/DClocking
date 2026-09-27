/** Trusted, dependency-free Cordis bridge; never evaluates model-generated code. */
export const name = 'dclocking-host-tools';
export const inject = ['tools', 'llm'];

export async function apply(ctx, config) {
  const base = process.env.DCLOCKING_TOOL_URL;
  const token = process.env.DCLOCKING_TOOL_TOKEN;
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base ?? '') || !token) {
    throw new Error('DClocking requires its authenticated loopback tool gateway');
  }
  const definitions = config.tools;
  const allowed = new Set(definitions.map(tool => tool.name));
  const agents = new Set();
  let runId;
  let stepId;
  let cancelledRunId;
  let settledRunId;
  const post = async (path, body, signal) => {
    const response = await fetch(base + path, {
      method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'},
      body: JSON.stringify(body), signal,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error ?? 'DClocking host rejected request');
    return result;
  };
  // Defence in depth: unknown tools remain forbidden even if an upstream
  // profile ever grows an unexpected producer.
  ctx.effect(() => ctx.tools.guard(exec => allowed.has(exec.name) ? undefined : 'DClocking tool is not permitted'));
  for (const definition of definitions) {
    ctx.effect(() => ctx.tools.register({
      ...definition,
      output: {schema: {type: 'string'}, render: (_args, value) => [{type: 'text', text: value}]},
      async execute(args, execution) {
        const result = await post('/tool', {
          name: definition.name, arguments: args, call_id: String(execution.callId),
          run_id: runId,
          step_id: stepId,
        }, execution.signal);
        return result.result;
      },
    }));
  }
  ctx.on('agent/created', ({agent}) => {
    agents.add(agent);
    agent.ctx.effect(() => agent.ctx.tools.restrict({allow: [...allowed]}));
  });
  ctx.on('agent/disposed', ({agent}) => { agents.delete(agent); });
  ctx.on('agent/status', ({status}) => {
    // running is emitted synchronously as followup() reserves the driver,
    // earlier than turn/start. Old control responses must not clear new input.
    if (status === 'running') runId = undefined;
  });
  ctx.on('session/event', (_session, event) => {
    if (event.type === 'turn/start') runId = undefined;
  });
  ctx.on('agent/request', async (_payload, next) => ({
    ...await next(), temperature: config.temperature,
  }));
  // The published Python SDK has no cancel RPC. Use the public Agent.cancel
  // capability through this trusted host-only control channel, preserving the
  // process and durable session rather than inventing an SDK wire method.
  const cancelRun = expectedRunId => {
    if (!expectedRunId || expectedRunId !== runId || cancelledRunId === expectedRunId) return;
    cancelledRunId = expectedRunId;
    for (const agent of agents) {
      // rc1 logs the supplied cause into turn/end. Node fetch may otherwise
      // mutate that object with a stack property, rejecting durable settlement
      // and poisoning the next turn. Keep the public cause JSON-immutable.
      if (agent.status === 'running') agent.cancel(Object.freeze({kind: 'user'}));
    }
  };
  let checking = false;
  const timer = setInterval(async () => {
    if (checking) return;
    checking = true;
    const expectedRunId = runId;
    try {
      const control = await post('/control', {}, AbortSignal.timeout(1000));
      if (control.settle && control.run_id && settledRunId !== control.run_id) {
        // Python holds its run lock until this ack, so no next prompt can
        // arrive between driver quiescence and retiring the cancellation nonce.
        await Promise.all([...agents].map(agent => agent.whenIdle()));
        runId = undefined;
        settledRunId = control.run_id;
        await post('/settled', {run_id: control.run_id}, AbortSignal.timeout(1000));
      } else if (control.cancel && control.run_id === expectedRunId) {
        cancelRun(expectedRunId);
      }
    } catch {
      // Fail closed only for the request's own run; a stale control timeout
      // cannot cancel a later turn. Repeated polls never re-clear the inbox.
      cancelRun(expectedRunId);
    } finally { checking = false; }
  }, 50);
  ctx.effect(() => () => clearInterval(timer));
  ctx.on('llm/stream', async function* (options, next) {
    // Checked before every provider request, not after a model round completes.
    const names = (options.tools ?? []).map(tool => tool.name).sort();
    if (JSON.stringify(names) !== JSON.stringify([...allowed].sort())) {
      throw new Error('DClocking refused an unexpected Harness tool inventory');
    }
    const step = await post('/step', {}, options.signal);
    runId = step.run_id;
    stepId = step.step_id;
    for await (const chunk of next()) {
      if (chunk.type === 'text-delta') await post('/text', {text: chunk.text, run_id: runId}, options.signal);
      yield chunk;
    }
  });
  await post('/ready', {names: ctx.tools.schemas().map(tool => tool.name).sort()});
}
