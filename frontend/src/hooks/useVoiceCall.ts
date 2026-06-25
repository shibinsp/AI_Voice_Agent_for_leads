import { useCallback, useEffect, useRef, useState } from "react";

import { getVoiceStreamUrlWithToken } from "../lib/api";
import type { QualificationResultRead, VoiceStreamMessage } from "../types/api";

export interface VoiceCallConnection {
  sessionId: number;
  token: string;
  language: string;
  openingTurns: string[];
}

export interface DisplayTurn {
  speaker: "agent" | "lead";
  text: string;
}

export type VoiceCallPhase =
  | "connecting"
  | "ready"
  | "recording"
  | "thinking"
  | "completed"
  | "error";

export type VoiceQualification = Pick<
  QualificationResultRead,
  "outcome" | "score" | "summary"
>;

export interface UseVoiceCallResult {
  phase: VoiceCallPhase;
  turns: DisplayTurn[];
  qualification: VoiceQualification | null;
  error: string | null;
  speechSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  endCall: () => void;
}

function getRecognitionCtor(): SpeechRecognitionConstructor | null {
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
}

/**
 * Drives one browser voice call: opens the WebSocket, captures speech with the Web Speech API
 * (STT), sends the transcript as text, and speaks each agent reply back (TTS). The `connect`
 * callback yields the session id + token (operator: create session + localStorage token;
 * enquiry: values from the public submit response).
 */
export function useVoiceCall(
  connect: () => Promise<VoiceCallConnection>,
  onCompleted?: () => void,
): UseVoiceCallResult {
  const [phase, setPhase] = useState<VoiceCallPhase>("connecting");
  const [turns, setTurns] = useState<DisplayTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [qualification, setQualification] = useState<VoiceQualification | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const langRef = useRef<string>("te-IN");
  const connectRef = useRef(connect);
  const completedRef = useRef(onCompleted);
  connectRef.current = connect;
  completedRef.current = onCompleted;

  const speechSupported = getRecognitionCtor() !== null;

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langRef.current;
    const base = langRef.current.split("-")[0];
    const voice = window.speechSynthesis
      .getVoices()
      .find((v) => v.lang === langRef.current || v.lang.startsWith(base));
    if (voice) utterance.voice = voice;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function run(): Promise<void> {
      try {
        const conn = await connectRef.current();
        if (cancelled) return;
        langRef.current = conn.language || "te-IN";
        if (conn.openingTurns.length > 0) {
          setTurns(conn.openingTurns.map((text) => ({ speaker: "agent" as const, text })));
        }

        const ws = new WebSocket(getVoiceStreamUrlWithToken(conn.sessionId, conn.token));
        wsRef.current = ws;
        ws.onmessage = (event) => {
          const message = JSON.parse(event.data) as VoiceStreamMessage;
          if (message.type === "ready") {
            setPhase("ready");
            const last = conn.openingTurns[conn.openingTurns.length - 1];
            if (last) speak(last);
          } else if (message.type === "turn") {
            setTurns((prev) => [
              ...prev,
              { speaker: "lead", text: message.lead_text },
              { speaker: "agent", text: message.agent_text },
            ]);
            setPhase("ready");
            speak(message.agent_text);
          } else if (message.type === "completed") {
            setQualification(message.qualification);
            setPhase("completed");
            completedRef.current?.();
          } else if (message.type === "error") {
            setError(message.detail);
            setPhase("error");
          }
        };
        ws.onerror = () => {
          if (!cancelled) {
            setError("Connection failed.");
            setPhase("error");
          }
        };
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to start the call");
          setPhase("error");
        }
      }
    }

    void run();
    return () => {
      cancelled = true;
      recognitionRef.current?.abort();
      recognitionRef.current = null;
      window.speechSynthesis?.cancel();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [speak]);

  const startListening = useCallback(() => {
    setPhase((current) => {
      if (current !== "ready") return current;
      const Ctor = getRecognitionCtor();
      if (!Ctor) {
        setError("Speech recognition is not supported in this browser. Try Chrome.");
        return current;
      }
      const recognition = new Ctor();
      recognition.lang = langRef.current;
      recognition.interimResults = false;
      recognition.continuous = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        const result = event.results[0]?.[0];
        const text = result?.transcript?.trim();
        if (text) {
          setPhase("thinking");
          wsRef.current?.send(
            JSON.stringify({ type: "text", text, confidence: result.confidence ?? null }),
          );
        } else {
          setPhase("ready");
        }
      };
      recognition.onerror = (event) => {
        setError(`Speech recognition error: ${event.error}`);
        setPhase("ready");
      };
      recognition.onend = () => {
        setPhase((p) => (p === "recording" ? "ready" : p));
      };
      recognitionRef.current = recognition;
      recognition.start();
      return "recording";
    });
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  const endCall = useCallback(() => {
    setPhase("thinking");
    window.speechSynthesis?.cancel();
    wsRef.current?.send(JSON.stringify({ type: "end" }));
  }, []);

  return {
    phase,
    turns,
    qualification,
    error,
    speechSupported,
    startListening,
    stopListening,
    endCall,
  };
}
