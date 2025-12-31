import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { v4 as uuidv4 } from "uuid";

interface Message {
  message: string;
  isUser: boolean;
  sources?: string[];
}

function App() {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  // Loading states
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const sessionIdRef = useRef<string>(uuidv4());

  useEffect(() => {
    sessionIdRef.current = uuidv4();
  }, []);

  // Handle streaming partial messages
  const setPartialMessage = (chunk: string, sources: string[] = []) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];

      if (!last || last.isUser) {
        return [...prev, { message: chunk, isUser: false, sources }];
      }

      return [
        ...prev.slice(0, -1),
        {
          message: last.message + chunk,
          isUser: false,
          sources: last.sources
            ? [...last.sources, ...sources]
            : sources,
        },
      ];
    });
  };

  function handleReceiveMessage(data: string) {
    const parsed = JSON.parse(data);

    if (parsed.answer) {
      setPartialMessage(parsed.answer.content);
    }

    if (parsed.docs) {
      setPartialMessage(
        "",
        parsed.docs.map((doc: any) => doc.metadata.source)
      );
    }
  }

  const handleSendMessage = async (message: string) => {
    if (!message) return;

    setIsSending(true);
    setInputValue("");
    setMessages((prev) => [...prev, { message, isUser: true }]);

    try {
      await fetchEventSource("http://127.0.0.1:8000/rag/stream", {
        method: "POST",
        openWhenHidden: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input: { question: message },
          config: {
            configurable: {
              sessionId: sessionIdRef.current,
            },
          },
        }),
        onmessage(event) {
          if (event.event === "data") {
            handleReceiveMessage(event.data);
          }
        },
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage(inputValue.trim());
    }
  };

  function formatSource(source: string) {
    return source.split("/").pop() || "";
  }

  const handleUploadFiles = async () => {
    if (!selectedFiles) return;

    setIsUploading(true);
    const formData = new FormData();

    Array.from(selectedFiles).forEach((file) => {
      formData.append("files", file);
    });

    try {
      await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const loadAndProcessPDFs = async () => {
    setIsProcessing(true);
    try {
      await fetch("http://127.0.0.1:8000/load-and-process-pdfs", {
        method: "POST",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="bg-blue-100 text-gray-800 text-center p-4 shadow-sm font-semibold">
        A Basic Chat With Your Private PDFs (RAG App)
      </header>

      <main className="flex-grow container mx-auto p-4 flex flex-col">
        <div className="flex-grow bg-white shadow sm:rounded-lg overflow-hidden">
          <div className="border-b border-gray-200 p-4 space-y-3">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg max-w-[80%] ${
                  msg.isUser
                    ? "bg-blue-50 ml-auto text-right"
                    : "bg-gray-50 mr-auto"
                }`}
              >
                <div className="text-gray-800 whitespace-pre-wrap">
                  {msg.message}
                </div>

                {!msg.isUser && msg.sources && msg.sources.length > 0 && (
                  <div className="text-xs mt-3">
                    <hr className="my-2 border-gray-200" />
                    {msg.sources.map((source, idx) => (
                      <div key={idx}>
                        <a
                          download
                          target="_blank"
                          rel="noreferrer"
                          href={`http://127.0.0.1:8000/rag/static/${encodeURI(
                            formatSource(source)
                          )}`}
                          className="text-blue-600 hover:underline"
                        >
                          {formatSource(source)}
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="p-4 bg-gray-50">
            <textarea
              className="w-full p-2 border rounded resize-none text-gray-800"
              placeholder="Enter your message..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
            />

            <button
              disabled={isSending}
              onClick={() => handleSendMessage(inputValue.trim())}
              className={`mt-2 px-4 py-2 rounded text-white font-bold ${
                isSending
                  ? "bg-gray-400"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {isSending ? "Thinking..." : "Send"}
            </button>

            <div className="mt-4">
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={(e) => setSelectedFiles(e.target.files)}
              />

              <button
                disabled={isUploading}
                onClick={handleUploadFiles}
                className={`mt-2 block px-4 py-2 rounded text-white font-bold ${
                  isUploading
                    ? "bg-gray-400"
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {isUploading ? "Uploading..." : "Upload PDFs"}
              </button>

              <button
                disabled={isProcessing}
                onClick={loadAndProcessPDFs}
                className={`mt-2 px-4 py-2 rounded text-white font-bold ${
                  isProcessing
                    ? "bg-gray-400"
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {isProcessing
                  ? "Processing PDFs..."
                  : "Load and Process PDFs"}
              </button>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-blue-100 text-gray-800 text-center p-3 text-xs border-t">
        © 2025 · RAG PDF Chat Application
      </footer>
    </div>
  );
}

export default App;
