<script>
    import { onMount, onDestroy } from "svelte";
    import { invoke } from "@tauri-apps/api/core";
    import { Terminal } from "xterm";
    import { FitAddon } from "xterm-addon-fit";
    import { WebLinksAddon } from "xterm-addon-web-links";
    import "xterm/css/xterm.css";

    export let initialContent = [
        "\x1b[1;34mMetatheos Governance Engine v0.5.0\x1b[0m",
        "Type \x1b[1;32mhelp\x1b[0m for available commands...",
        "",
    ];

    let terminalContainer;
    let terminal;
    let fitAddon;
    let resizeObserver;
    let buffer = "";

    function prompt() {
        if (terminal) {
            terminal.write("\r\n$ ");
        }
    }

    async function executeCurrent() {
        const cmd = buffer.trim();
        buffer = "";
        if (!cmd) {
            prompt();
            return;
        }
        if (cmd === "clear") {
            terminal.reset();
            initialContent.forEach((line) => terminal.writeln(line));
            terminal.write("\r\n$ ");
            return;
        }
        try {
            const result = await invoke("execute_shell_command", { input: cmd });
            terminal.writeln("");
            if (result.output) {
                terminal.writeln(result.output);
            }
            if (result.error) {
                terminal.writeln(`\x1b[31m${result.error}\x1b[0m`);
            }
        } catch (err) {
            terminal.writeln("");
            terminal.writeln(`\x1b[31m${err}\x1b[0m`);
        }
        prompt();
    }

    onMount(() => {
        // Initialize xterm.js
        terminal = new Terminal({
            cursorBlink: true,
            theme: {
                background: "#111827", // gray-900
                foreground: "#e5e7eb", // gray-200
                cursor: "#60a5fa", // blue-400
                selectionBackground: "#374151",
                black: "#000000",
                red: "#ef4444",
                green: "#22c55e",
                yellow: "#eab308",
                blue: "#3b82f6",
                magenta: "#d946ef",
                cyan: "#06b6d4",
                white: "#ffffff",
                brightBlack: "#4b5563",
                brightRed: "#f87171",
                brightGreen: "#4ade80",
                brightYellow: "#fde047",
                brightBlue: "#60a5fa",
                brightMagenta: "#e879f9",
                brightCyan: "#22d3ee",
                brightWhite: "#ffffff",
            },
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            fontSize: 13,
            lineHeight: 1.2,
        });

        // Addons
        fitAddon = new FitAddon();
        terminal.loadAddon(fitAddon);
        terminal.loadAddon(new WebLinksAddon());

        // Open in DOM
        terminal.open(terminalContainer);
        fitAddon.fit();

        // Initial Content
        initialContent.forEach((line) => terminal.writeln(line));
        terminal.write("\r\n$ ");

        // Input Handling (real command dispatcher)
        terminal.onData((e) => {
            const char = e;
            if (char === "\r") {
                executeCurrent();
            } else if (char === "\u0003") {
                // Ctrl+C
                buffer = "";
                terminal.writeln("^C");
                prompt();
            } else if (char === "\u007F") {
                // Backspace
                if (buffer.length > 0) {
                    buffer = buffer.slice(0, -1);
                    terminal.write("\b \b");
                }
            } else {
                buffer += char;
                terminal.write(char);
            }
        });

        // Resize Observer to auto-fit
        resizeObserver = new ResizeObserver(() => {
            fitAddon.fit();
        });
        resizeObserver.observe(terminalContainer);
    });

    onDestroy(() => {
        if (terminal) terminal.dispose();
        if (resizeObserver) resizeObserver.disconnect();
    });

    // Exposed method to write logs externally
    export function writeLog(message) {
        if (terminal) {
            terminal.writeln(`\x1b[2m[LOG]\x1b[0m ${message}`);
            terminal.write("$ ");
            buffer = "";
        }
    }
</script>

<div class="terminal-wrapper" bind:this={terminalContainer}></div>

<style>
    .terminal-wrapper {
        width: 100%;
        height: 100%;
        background-color: #111827;
        padding: 4px 0 0 8px; /* Slight padding */
        overflow: hidden;
    }

    /* Hide scrollbar if needed or stylize it */
    :global(.xterm-viewport) {
        overflow-y: auto;
    }
</style>
