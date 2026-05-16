VoxEngine.addEventListener(AppEvents.Started, function () {
  const rawCustomData = VoxEngine.customData();
  Logger.write("customData raw: " + rawCustomData);

  let customData;
  try {
    customData = JSON.parse(rawCustomData || "{}");
  } catch (e) {
    Logger.write("Invalid custom data: " + e);
    VoxEngine.terminate();
    return;
  }

  const destination = customData.destination;
  const callerId    = customData.callerId;
  const audioUrl    = customData.audioUrl;

  if (!destination || !callerId || !audioUrl) {
    Logger.write("Missing required custom data: " + rawCustomData);
    VoxEngine.terminate();
    return;
  }

  let playbackFinished = false;
  const call = destination.includes('@')
    ? VoxEngine.callUser(destination.split('@')[0], callerId)
    : VoxEngine.callPSTN(destination, callerId);

  call.addEventListener(CallEvents.Connected, function () {
    Logger.write("Connected to " + destination + ". Playing: " + audioUrl);
    call.startPlayback(audioUrl);
  });

  call.addEventListener(CallEvents.PlaybackFinished, function () {
    playbackFinished = true;
    Logger.write("Playback finished. Hanging up.");
    call.hangup();
  });

  call.addEventListener(CallEvents.Failed, function (e) {
    Logger.write("Call failed: " + JSON.stringify(e));
    VoxEngine.terminate();
  });

  call.addEventListener(CallEvents.Disconnected, function () {
    Logger.write(playbackFinished ? "Call completed." : "Disconnected.");
    VoxEngine.terminate();
  });
});
