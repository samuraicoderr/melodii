/**
 * Audio preprocessing utilities for client-side audio manipulation.
 * Uses the Web Audio API to inspect duration and extract clips.
 */

const CLIP_DURATION_SECONDS = 30;

/**
 * Error types for audio preprocessing failures.
 */
export class AudioProcessingError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'AudioProcessingError';
  }
}

/**
 * Gets the duration of an audio file in seconds.
 * @param file - The audio file to inspect
 * @returns Duration in seconds
 * @throws AudioProcessingError if decoding fails
 */
async function getAudioDuration(file: File): Promise<number> {
  const arrayBuffer = await file.arrayBuffer();
  const audioContext = new AudioContext();
  
  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    return audioBuffer.duration;
  } catch (error) {
    throw new AudioProcessingError('Failed to decode audio file', error);
  } finally {
    await audioContext.close();
  }
}

/**
 * Extracts a clip from an audio buffer.
 * @param audioBuffer - The source audio buffer
 * @param startTime - Start time in seconds
 * @param duration - Duration in seconds
 * @returns A new AudioBuffer containing the clip
 */
function extractClip(audioBuffer: AudioBuffer, startTime: number, duration: number): AudioBuffer {
  const sampleRate = audioBuffer.sampleRate;
  const startSample = Math.floor(startTime * sampleRate);
  const endSample = Math.min(startSample + Math.floor(duration * sampleRate), audioBuffer.length);
  const clipLength = endSample - startSample;
  
  const clipBuffer = new AudioContext().createBuffer(
    audioBuffer.numberOfChannels,
    clipLength,
    sampleRate
  );
  
  for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
    const channelData = audioBuffer.getChannelData(channel);
    const clipChannelData = clipBuffer.getChannelData(channel);
    
    for (let i = 0; i < clipLength; i++) {
      clipChannelData[i] = channelData[startSample + i];
    }
  }
  
  return clipBuffer;
}

/**
 * Encodes an AudioBuffer to a WAV file.
 * @param audioBuffer - The audio buffer to encode
 * @returns A Blob containing WAV data
 */
function audioBufferToWav(audioBuffer: AudioBuffer): Blob {
  const numberOfChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const format = 1; // PCM
  const bitDepth = 16;
  
  const bytesPerSample = bitDepth / 8;
  const blockAlign = numberOfChannels * bytesPerSample;
  
  const dataLength = audioBuffer.length * blockAlign;
  const bufferLength = 44 + dataLength;
  
  const arrayBuffer = new ArrayBuffer(bufferLength);
  const view = new DataView(arrayBuffer);
  
  // WAV header
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + dataLength, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, format, true);
  view.setUint16(22, numberOfChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, 'data');
  view.setUint32(40, dataLength, true);
  
  // Write audio data
  const channels: Float32Array[] = [];
  for (let i = 0; i < numberOfChannels; i++) {
    channels.push(audioBuffer.getChannelData(i));
  }
  
  let offset = 44;
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, channels[channel][i]));
      const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(offset, intSample, true);
      offset += 2;
    }
  }
  
  return new Blob([arrayBuffer], { type: 'audio/wav' });
}

function writeString(view: DataView, offset: number, string: string): void {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

/**
 * Preprocesses an audio file for genre classification.
 * - If duration <= 30 seconds, returns the original file unchanged.
 * - If duration > 30 seconds, extracts a 30-second clip centered around the middle.
 * 
 * @param file - The audio file to preprocess
 * @returns A File ready for upload (original or clipped)
 * @throws AudioProcessingError if processing fails
 */
export async function preprocessAudioForClassification(file: File): Promise<File> {
  // Validate file type
  if (!file.type.startsWith('audio/')) {
    throw new AudioProcessingError('File is not an audio file');
  }
  
  // Get duration
  const duration = await getAudioDuration(file);
  
  // If duration is within limit, return original
  if (duration <= CLIP_DURATION_SECONDS) {
    return file;
  }
  
  // Calculate clip boundaries (centered around middle)
  const middle = duration / 2;
  const startTime = Math.max(0, middle - CLIP_DURATION_SECONDS / 2);
  const clipDuration = Math.min(CLIP_DURATION_SECONDS, duration - startTime);
  
  // Decode audio
  const arrayBuffer = await file.arrayBuffer();
  const audioContext = new AudioContext();
  
  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    // Extract clip
    const clipBuffer = extractClip(audioBuffer, startTime, clipDuration);
    
    // Encode to WAV
    const wavBlob = audioBufferToWav(clipBuffer);
    
    // Create new File with appropriate name
    const originalName = file.name;
    const lastDotIndex = originalName.lastIndexOf('.');
    const baseName = lastDotIndex !== -1 ? originalName.slice(0, lastDotIndex) : originalName;
    const newName = `${baseName}_clip.wav`;
    
    return new File([wavBlob], newName, { type: 'audio/wav' });
  } catch (error) {
    throw new AudioProcessingError('Failed to extract audio clip', error);
  } finally {
    await audioContext.close();
  }
}
