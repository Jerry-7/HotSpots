import React, { useEffect, useRef, useState } from "react";

// Note: This code demonstrates the structure. 
// In a real React project, you would install xterm.js:
// npm install xterm xterm-addon-fit
// and import the actual libraries as shown in the commented lines below.
// The mock implementation here simulates the API for demonstration.

// --- Mock xterm.js implementation for demonstration ---
// In a real project, replace this with:
// import { Terminal } from "xterm";
// import { FitAddon } from "xterm-addon-fit";
// import "xterm/css/xterm.css";

// Mock Terminal class
class MockTerminal {
  constructor(options) {
    this.options = options;
    this.element = null;
    this.onDataCallback = null;
    this.addons = []; // Track loaded addons
  }

  open(container) {
    console.log("Mock Terminal: open called on", container);
    this.element = container;
    if (this.element) {
      // Simulate a basic terminal-like div
      const termDiv = document.createElement('div');
      termDiv.id = 'mock-terminal-output';
      termDiv.style.cssText = `
        width: 100%;
        height: 100%;
        background-color: #000;
        color: #fff;
        font-family: monospace;
        white-space: pre;
        overflow: auto;
        padding: 10px;
        outline: none; /* Remove focus outline */
        cursor: text; /* Show text cursor */
      `;
      termDiv.tabIndex = 0; // Make div focusable
      this.element.appendChild(termDiv);
      console.log("Mock terminal UI created");
      
      // Attach key event listeners directly to the terminal element
      termDiv.addEventListener('keydown', this.handleKeyDown.bind(this));
      termDiv.addEventListener('mousedown', (e) => {
          // Prevent default to avoid losing focus on click inside terminal
          e.preventDefault();
          termDiv.focus(); // Ensure it gets focus on click
          console.log("Terminal clicked, focused");
      });
      termDiv.addEventListener('blur', () => {
          console.log("Terminal lost focus");
      });
      termDiv.addEventListener('focus', () => {
          console.log("Terminal gained focus");
      });
    }
  }

  write(data) {
    console.log("Mock Terminal: write", data);
    const output = document.getElementById('mock-terminal-output');
    if (output) {
      output.textContent += data;
      output.scrollTop = output.scrollHeight; // Auto-scroll
    }
  }

  writeln(data) {
    this.write(data + '\n');
  }

  onData(callback) {
    this.onDataCallback = callback;
    console.log("Mock Terminal: onData handler set to", callback);
  }

  focus() {
    console.log("Mock Terminal: focus called");
    const output = document.getElementById('mock-terminal-output');
    if (output) {
      output.focus();
    }
  }

  dispose() {
    console.log("Mock Terminal: dispose called");
    const output = document.getElementById('mock-terminal-output');
    if (output && output.parentNode) {
      output.parentNode.removeChild(output);
    }
  }

  setOption(key, value) {
    console.log(`Mock Terminal: setOption ${key} = ${value}`);
    this.options[key] = value;
  }

  // Add the missing loadAddon method
  loadAddon(addon) {
     console.log("Mock Terminal: loadAddon called with", addon.constructor.name);
     this.addons.push(addon);
     // Call the addon's activate method, passing the terminal instance
     if (typeof addon.activate === 'function') {
         addon.activate(this);
     } else {
         console.warn("Addon does not have an activate method:", addon);
     }
  }
  
  // Handle keydown events
  handleKeyDown(e) {
      e.preventDefault(); // Prevent default browser actions
      console.log("Mock Terminal: Key pressed", e.key, e);
      if (this.onDataCallback) {
          // Convert key to a simple char or control sequence
          let char = e.key;
          if (e.key === 'Enter') char = '\r'; // Use \r for Enter in terminals
          else if (e.key === 'Backspace') char = '\x7f'; // Use \x7f for Backspace/Delete
          else if (e.key === 'Tab') char = '\t';
          else if (e.key === 'Escape') char = '\x1b'; // ESC key
          else if (e.ctrlKey) {
              // Basic control key handling (e.g., Ctrl+C -> \x03)
              // Map Ctrl+letter to ASCII control codes (0-31)
              if (e.key.length === 1 && e.key >= 'a' && e.key <= 'z') {
                  char = String.fromCharCode(e.keyCode - 64); // A=65->1, B=66->2, ..., Z=90->26
              } else if (e.key === ' ') {
                  char = '\x00'; // Ctrl+Space
              }
          } else if (e.key.length === 1) {
              // Only pass single printable characters
              // char is already e.key
          } else {
              // For keys like ArrowUp, Home, etc., you might want to send escape sequences
              // For simplicity, we'll just ignore them here or map common ones
              switch(e.key) {
                 case 'ArrowUp': char = '\x1b[A'; break;
                 case 'ArrowDown': char = '\x1b[B'; break;
                 case 'ArrowRight': char = '\x1b[C'; break;
                 case 'ArrowLeft': char = '\x1b[D'; break;
                 case 'Home': char = '\x1b[H'; break;
                 case 'End': char = '\x1b[F'; break;
                 default: char = ''; // Ignore other keys
              }
          }
          
          if (char) {
              console.log("Mock Terminal: Sending data via onData callback:", char);
              this.onDataCallback(char);
          }
      } else {
          console.log("Mock Terminal: onDataCallback not set, cannot send key data");
      }
  }
}

// Mock FitAddon class
class MockFitAddon {
  activate(terminal) {
    console.log("Mock FitAddon: activated on terminal");
    this.terminal = terminal;
  }

  fit() {
    console.log("Mock FitAddon: fit called");
    // Simulate fitting to container
    if (this.terminal.element) {
      const rect = this.terminal.element.getBoundingClientRect();
      console.log(`Mock FitAddon: fitted to ${rect.width}x${rect.height}`);
    }
  }

  proposeDimensions() {
    // Simulate proposing dimensions based on container size
    if (this.terminal.element) {
      const rect = this.terminal.element.getBoundingClientRect();
      return { cols: Math.floor(rect.width / 8), rows: Math.floor((rect.height - 20) / 16) }; // Rough estimate
    }
    return { cols: 80, rows: 24 };
  }

  dispose() {
    console.log("Mock FitAddon: dispose called");
  }
}
// --- End Mock ---

const App = () => {
  const terminalRef = useRef(null);
  const wsRef = useRef(null);
  const termRef = useRef(null);
  const fitAddonRef = useRef(null);
  const [host, setHost] = useState("192.168.0.113");
  const [username, setUsername] = useState("root");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Use mock classes for demonstration
    // In a real project, import the actual libraries:
    // const { Terminal } = await import('xterm');
    // const { FitAddon } = await import('xterm-addon-fit');
    const Term = MockTerminal; // Replace with `Terminal` in real project
    const FitAddon = MockFitAddon; // Replace with `FitAddon` in real project

    const termInstance = new Term({ cursorBlink: true, theme: { background: '#000', foreground: '#fff' } });
    const fitAddonInstance = new FitAddon();
    
    termInstance.loadAddon(fitAddonInstance);
    termInstance.open(terminalRef.current);
    fitAddonInstance.fit();
    termInstance.focus(); // Focus the terminal element initially

    termRef.current = termInstance;
    fitAddonRef.current = fitAddonInstance;

    termInstance.writeln("=== SSH Web Terminal ===");

    return () => {
      termInstance.dispose();
      fitAddonInstance.dispose();
    };
  }, []);

  const connectSSH = () => {
    if (isConnected || isReady) return; // Prevent multiple connections if already connected/ready

    const ws = new WebSocket("ws://localhost:8765"); // Use wss:// for production
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      setStatus("Connecting...");
      const connectMsg = JSON.stringify({
        type: "connect",
        host,
        username,
        password,
        port: 22
      });
      ws.send(connectMsg);
      // CRITICAL: Set isConnected to true *after* sending the connect message
      // This signals that the WebSocket is open and we are waiting for backend response
      console.log("Setting isConnected = true in onopen");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      console.log("Received message from server:", event.data); // Log raw message
      console.log("Current state - isConnected:", isConnected, "isReady:", isReady); // Log state at message receipt
      
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          console.log("Parsed message:", msg); // Log parsed message
          
          if (msg.type === 'status') {
            termRef.current.writeln(msg.message);
            // Keep status for user feedback, but don't set ready based on this anymore
            if (msg.message.includes("已连接")) {
               setStatus("Connected (waiting for ready signal)");
            }
          } else if (msg.type === 'ready') {
             // NEW: Handle the 'ready' message from the backend
             if (isConnected && !isReady) { // isConnected must be true AND isReady must be false
                 console.log("Ready message received. Setting isReady=true.");
                 setIsReady(true); // Set ready state to true upon receiving 'ready' message
                 setStatus("Connected & Ready for Input");
                 setTimeout(() => { // Use setTimeout to ensure DOM updates
                     console.log("Attempting to focus terminal after setting ready via 'ready' message...");
                     termRef.current.focus(); // Refocus terminal after state change
                 }, 0);
             }
          } else if (msg.type === 'error') {
            setStatus(`Error: ${msg.message}`);
            termRef.current.writeln(`\r\n--- ${msg.message} ---`);
            // If an error occurs, connection might be lost
            setIsConnected(false);
            setIsReady(false);
          } else if (msg.type === 'output') {
             // Handle general output (shouldn't happen anymore as 'ready' takes precedence for first data)
             console.log("Received output data, writing to terminal.");
             termRef.current.write(msg.data);
             // Fallback: Check if we are connected but not yet ready upon receiving first output (less reliable than 'ready' message)
             if (isConnected && !isReady) {
                console.log("Output message received while connected but not ready (fallback). Setting isReady=true.");
                setIsReady(true);
                setStatus("Connected & Ready for Input");
                setTimeout(() => {
                    console.log("Attempting to focus terminal after setting ready via fallback output...");
                    termRef.current.focus();
                }, 0);
             }
          } else {
              console.log("Unknown message type received:", msg.type);
          }
        } catch (e) {
          console.error("Error parsing JSON message:", e);
          console.log("Raw message was:", event.data);
          // Assume it's raw output if not JSON (shouldn't happen with new backend)
          termRef.current.write(event.data);
          // Fallback: Check if we are connected but not yet ready upon receiving raw output
           if (isConnected && !isReady) {
               console.log("Raw output received while connected but not ready (fallback). Setting isReady=true.");
               setIsReady(true);
               setStatus("Connected & Ready for Input");
               setTimeout(() => {
                   console.log("Attempting to focus terminal after setting ready via fallback raw output...");
                   termRef.current.focus();
               }, 0);
           }
        }
      } else {
        console.log("Received binary data, writing to terminal.");
        termRef.current.write(new TextDecoder().decode(event.data));
        // Fallback: Check if we are connected but not yet ready upon receiving binary output
         if (isConnected && !isReady) {
             console.log("Binary output received while connected but not ready (fallback). Setting isReady=true.");
             setIsReady(true);
             setStatus("Connected & Ready for Input");
             setTimeout(() => {
                 console.log("Attempting to focus terminal after setting ready via fallback binary output...");
                 termRef.current.focus();
             }, 0);
         }
      }
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed", event);
      setIsConnected(false);
      setIsReady(false); // Reset ready state on close
      setStatus("Disconnected");
      termRef.current.writeln("\r\n--- Connection Closed ---");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setStatus("Connection Error");
      termRef.current.writeln("\r\n--- Connection Error ---");
      setIsConnected(false); // Also reset connected state on error
      setIsReady(false);
    };

    termRef.current.onData(data => {
      console.log("Terminal sent data:", data);
      // Check if WebSocket is open and ready for input
      if (isReady && ws && ws.readyState === WebSocket.OPEN) {
        const inputMsg = JSON.stringify({ type: "input", data: data });
        ws.send(inputMsg);
        console.log("Sent input to server:", data);
      } else {
          // Provide more specific reason for discarding input
          console.log("Current state during input attempt - isConnected:", isConnected, "isReady:", isReady, "WS State:", ws ? ws.readyState : 'N/A');
          if (!isReady) {
              console.log("Input discarded - Terminal not ready (isReady is false).");
          } else if (!ws || ws.readyState !== WebSocket.OPEN) {
              console.log("Input discarded - WebSocket not open (readyState:", ws ? ws.readyState : 'N/A', ").");
          } else {
              console.log("Input discarded - Unexpected state.");
          }
      }
    });

    const handleResize = () => {
      if (isReady && fitAddonRef.current) {
        fitAddonRef.current.fit();
        const dims = fitAddonRef.current.proposeDimensions();
        if (dims && ws && ws.readyState === WebSocket.OPEN) {
          const resizeMsg = JSON.stringify({ type: "resize", cols: dims.cols, rows: dims.rows });
          ws.send(resizeMsg);
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  };

  const disconnectSSH = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const disconnectMsg = JSON.stringify({ type: "disconnect" });
      wsRef.current.send(disconnectMsg);
    }
  };

  // Effect to refocus terminal if it loses focus while connected and ready
  useEffect(() => {
      if (isReady && termRef.current) {
          const terminalElement = document.getElementById('mock-terminal-output'); // Get the actual div
          if (terminalElement) {
              const handleFocusLoss = (e) => {
                  if (!terminalElement.contains(e.relatedTarget)) {
                      console.log("Focus lost from terminal, refocusing...");
                      setTimeout(() => terminalElement.focus(), 0); // Delay refocus
                  }
              };
              document.addEventListener('focusout', handleFocusLoss);
              return () => {
                  document.removeEventListener('focusout', handleFocusLoss);
              };
          }
      }
  }, [isReady]); // Re-run if isReady changes


  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Web SSH Terminal</h1>
      <div style={{ marginBottom: "10px" }}>
        <input
          value={host}
          onChange={(e) => setHost(e.target.value)}
          placeholder="Host"
          style={{ padding: "5px", marginRight: "10px" }}
        />
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={{ padding: "5px", marginRight: "10px" }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          style={{ padding: "5px", marginRight: "10px" }}
        />
        <button 
          onClick={connectSSH} 
          disabled={isConnected}
          style={{ padding: "5px 10px", marginRight: "5px" }}
        >
          Connect
        </button>
        <button 
          onClick={disconnectSSH} 
          disabled={!isConnected}
          style={{ padding: "5px 10px" }}
        >
          Disconnect
        </button>
      </div>
      <div 
        ref={terminalRef} 
        style={{ 
          height: "70vh", 
          width: "100%", 
          border: "1px solid #ccc", 
          background: "#000",
          marginBottom: "10px",
          outline: "none" // Remove default outline when focused
        }} 
      />
      <div>Status: {status}</div>
    </div>
  );
};

export default App;



