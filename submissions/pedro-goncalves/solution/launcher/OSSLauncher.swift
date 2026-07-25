import AppKit
import Darwin
import Foundation

final class OSSLauncher: NSObject, NSApplicationDelegate {
    private let ink = NSColor(
        calibratedRed: 0.02,
        green: 0.13,
        blue: 0.18,
        alpha: 1
    )
    private let muted = NSColor(
        calibratedRed: 0.34,
        green: 0.39,
        blue: 0.43,
        alpha: 1
    )
    private let surface = NSColor(
        calibratedRed: 0.95,
        green: 0.96,
        blue: 0.97,
        alpha: 1
    )
    private let gold = NSColor(
        calibratedRed: 0.77,
        green: 0.58,
        blue: 0.32,
        alpha: 1
    )
    private let danger = NSColor(
        calibratedRed: 0.63,
        green: 0.19,
        blue: 0.16,
        alpha: 1
    )
    private let root = Bundle.main.bundleURL
        .deletingLastPathComponent()
        .deletingLastPathComponent()
    private var processes: [Process] = []
    private var ollamaStartedHere = false
    private var publicURL = ""

    private var window: NSWindow!
    private let status = NSTextField(labelWithString: "Pronto para iniciar")
    private let link = NSTextField(labelWithString: "O link aparecerá aqui")
    private let progress = NSProgressIndicator()
    private let accessPassword = NSSecureTextField()
    private let start = NSButton(title: "Ligar OSS", target: nil, action: nil)
    private let copyLink = NSButton(title: "Copiar link", target: nil, action: nil)
    private let openLink = NSButton(title: "Abrir OSS", target: nil, action: nil)
    private let stop = NSButton(title: "Desligar", target: nil, action: nil)
    private var steps: [NSTextField] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.applicationIconImage = makeIcon(size: 512)
        buildWindow()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { self.launch() }
    }

    func applicationShouldTerminateAfterLastWindowClosed(
        _ sender: NSApplication
    ) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        stopAll()
    }

    private func buildWindow() {
        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 680, height: 560),
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.title = "OSS"
        window.center()
        window.appearance = NSAppearance(named: .aqua)
        window.backgroundColor = .white

        let content = NSView()
        content.translatesAutoresizingMaskIntoConstraints = false
        content.wantsLayer = true
        content.layer?.backgroundColor = NSColor.white.cgColor
        window.contentView = content

        let title = NSTextField(labelWithString: "OSS")
        title.font = .systemFont(ofSize: 30, weight: .bold)
        title.textColor = ink
        let subtitle = NSTextField(
            labelWithString: "Operating System for Support. Challenge 002"
        )
        subtitle.font = .systemFont(ofSize: 13)
        subtitle.textColor = muted
        let heading = NSStackView(views: [title, subtitle])
        heading.orientation = .vertical
        heading.alignment = .leading
        heading.spacing = 4

        let stepNames = [
            "1. Verificar componentes",
            "2. Iniciar Granite local",
            "3. Iniciar sistema de suporte",
            "4. Publicar link temporário",
        ]
        steps = stepNames.map {
            let label = NSTextField(labelWithString: "○  \($0)")
            label.font = .systemFont(ofSize: 13, weight: .medium)
            label.textColor = muted
            return label
        }
        let stepStack = NSStackView(views: steps)
        stepStack.orientation = .vertical
        stepStack.alignment = .leading
        stepStack.spacing = 13

        progress.style = .spinning
        progress.controlSize = .small
        progress.isHidden = true
        status.font = .systemFont(ofSize: 13, weight: .semibold)
        status.textColor = ink
        let statusRow = NSStackView(views: [progress, status])
        statusRow.orientation = .horizontal
        statusRow.spacing = 8

        let passwordTitle = NSTextField(
            labelWithString: "SENHA TEMPORÁRIA DE ACESSO"
        )
        passwordTitle.font = .systemFont(ofSize: 10, weight: .bold)
        passwordTitle.textColor = muted
        accessPassword.placeholderString = "Defina uma senha para esta sessão"
        accessPassword.stringValue =
            ProcessInfo.processInfo.environment["OSS_ACCESS_PASSWORD"] ?? ""
        accessPassword.font = .systemFont(ofSize: 13)
        accessPassword.controlSize = .large
        let passwordStack = NSStackView(views: [passwordTitle, accessPassword])
        passwordStack.orientation = .vertical
        passwordStack.alignment = .leading
        passwordStack.spacing = 7

        let linkTitle = NSTextField(labelWithString: "LINK TEMPORÁRIO")
        linkTitle.font = .systemFont(ofSize: 10, weight: .bold)
        linkTitle.textColor = muted
        link.font = .monospacedSystemFont(ofSize: 12, weight: .medium)
        link.textColor = NSColor(
            calibratedRed: 0.02,
            green: 0.27,
            blue: 0.36,
            alpha: 1
        )
        link.lineBreakMode = .byTruncatingMiddle
        let result = NSStackView(views: [linkTitle, link])
        result.orientation = .vertical
        result.alignment = .leading
        result.spacing = 7
        result.edgeInsets = NSEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
        result.wantsLayer = true
        result.layer?.backgroundColor = surface.cgColor
        result.layer?.cornerRadius = 8
        result.layer?.borderWidth = 1
        result.layer?.borderColor = NSColor(
            calibratedRed: 0.83,
            green: 0.86,
            blue: 0.88,
            alpha: 1
        ).cgColor

        configure(start, #selector(launch), background: ink, foreground: .white)
        configure(copyLink, #selector(copyPublicLink), background: ink, foreground: .white)
        configure(openLink, #selector(openPublicLink), background: gold, foreground: ink)
        configure(stop, #selector(stopAndReset), background: danger, foreground: .white)
        [copyLink, openLink, stop].forEach { $0.isEnabled = false }
        let actions = NSStackView(views: [copyLink, openLink, stop])
        actions.orientation = .horizontal
        actions.distribution = .fillEqually
        actions.spacing = 8

        let main = NSStackView(
            views: [
                heading,
                separator(),
                stepStack,
                passwordStack,
                statusRow,
                result,
                start,
                actions,
            ]
        )
        main.orientation = .vertical
        main.alignment = .leading
        main.spacing = 16
        main.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(main)

        NSLayoutConstraint.activate([
            main.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 34),
            main.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -34),
            main.topAnchor.constraint(equalTo: content.topAnchor, constant: 32),
            accessPassword.widthAnchor.constraint(equalTo: main.widthAnchor),
            result.widthAnchor.constraint(equalTo: main.widthAnchor),
            start.widthAnchor.constraint(equalTo: main.widthAnchor),
            actions.widthAnchor.constraint(equalTo: main.widthAnchor),
        ])
    }

    private func configure(
        _ button: NSButton,
        _ action: Selector,
        background: NSColor,
        foreground: NSColor
    ) {
        button.target = self
        button.action = action
        button.bezelStyle = .rounded
        button.controlSize = .large
        button.font = .systemFont(ofSize: 13, weight: .semibold)
        styleButton(
            button,
            title: button.title,
            background: background,
            foreground: foreground
        )
    }

    private func styleButton(
        _ button: NSButton,
        title: String,
        background: NSColor,
        foreground: NSColor
    ) {
        button.title = title
        button.bezelColor = background
        button.contentTintColor = foreground
        button.attributedTitle = NSAttributedString(
            string: title,
            attributes: [
                .font: NSFont.systemFont(ofSize: 13, weight: .semibold),
                .foregroundColor: foreground,
            ]
        )
    }

    private func separator() -> NSBox {
        let box = NSBox()
        box.boxType = .separator
        return box
    }

    @objc private func launch() {
        let sessionPassword = accessPassword.stringValue
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !sessionPassword.isEmpty else {
            status.stringValue = "Defina uma senha temporária para iniciar."
            return
        }
        stopAll()
        publicURL = ""
        start.isEnabled = false
        accessPassword.isEnabled = false
        progress.isHidden = false
        progress.startAnimation(nil)
        resetSteps()
        setStatus("Verificando componentes...")

        DispatchQueue.global(qos: .userInitiated).async {
            guard let uv = self.executable([
                FileManager.default.homeDirectoryForCurrentUser
                    .appendingPathComponent(".local/bin/uv").path,
                "/opt/homebrew/bin/uv",
                "/usr/local/bin/uv",
            ]),
            let ollama = self.executable([
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
            ]),
            let cloudflared = self.executable([
                self.root.appendingPathComponent(".tools/cloudflared").path,
                "/opt/homebrew/bin/cloudflared",
                "/usr/local/bin/cloudflared",
            ]),
            FileManager.default.fileExists(
                atPath: self.root.appendingPathComponent("app.py").path
            ) else {
                return self.fail("Componentes do OSS não foram encontrados.")
            }

            self.markStep(0)
            self.setStatus("Iniciando Granite local...")
            if !self.waitFor("http://127.0.0.1:11434/api/tags", seconds: 2) {
                let process = self.makeProcess(
                    executable: ollama,
                    arguments: ["serve"],
                    directory: self.root,
                    environment: [:]
                )
                self.processes.append(process)
                self.ollamaStartedHere = true
                try? process.run()
            }
            guard self.waitFor("http://127.0.0.1:11434/api/tags", seconds: 20) else {
                return self.fail("Ollama não respondeu.")
            }
            self.markStep(1)

            self.setStatus("Iniciando sistema de suporte...")
            let streamlit = self.makeProcess(
                executable: uv,
                arguments: [
                    "run", "streamlit", "run", "app.py",
                    "--server.address", "127.0.0.1",
                    "--server.port", "8504",
                    "--server.headless", "true",
                ],
                directory: self.root,
                environment: [
                    "OSS_ACCESS_PASSWORD": sessionPassword,
                    "OSS_LOCAL_MODEL": "ibm/granite4.1:8b",
                ]
            )
            self.processes.append(streamlit)
            try? streamlit.run()
            guard self.waitFor("http://127.0.0.1:8504", seconds: 40) else {
                return self.fail("O OSS não respondeu na porta 8504.")
            }
            self.markStep(2)

            self.setStatus("Criando link HTTPS temporário...")
            let tunnel = self.makeProcess(
                executable: cloudflared,
                arguments: [
                    "tunnel", "--url", "http://127.0.0.1:8504",
                    "--no-autoupdate",
                ],
                directory: self.root,
                environment: [:]
            )
            let pipe = Pipe()
            tunnel.standardOutput = pipe
            tunnel.standardError = pipe
            pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
                let text = String(
                    data: handle.availableData,
                    encoding: .utf8
                ) ?? ""
                guard let match = text.range(
                    of: #"https://[a-z0-9-]+\.trycloudflare\.com"#,
                    options: .regularExpression
                ) else { return }
                self?.ready(baseURL: String(text[match]))
            }
            self.processes.append(tunnel)
            do {
                try tunnel.run()
            } catch {
                self.fail("Não foi possível iniciar o túnel temporário.")
            }
        }
    }

    private func ready(baseURL: String) {
        DispatchQueue.main.async {
            guard self.publicURL.isEmpty else { return }
            self.publicURL = baseURL
            self.markStep(3)
            self.link.stringValue = self.publicURL
            self.status.stringValue = "OSS online com Granite local"
            self.progress.stopAnimation(nil)
            self.progress.isHidden = true
            self.styleButton(
                self.start,
                title: "Reiniciar OSS",
                background: self.ink,
                foreground: .white
            )
            self.start.isEnabled = true
            self.accessPassword.isEnabled = true
            [self.copyLink, self.openLink, self.stop].forEach {
                $0.isEnabled = true
            }
            try? self.publicURL.write(
                to: self.root.appendingPathComponent(".oss-session-url"),
                atomically: true,
                encoding: .utf8
            )
        }
    }

    private func executable(_ candidates: [String]) -> URL? {
        candidates.first {
            FileManager.default.isExecutableFile(atPath: $0)
        }.map(URL.init(fileURLWithPath:))
    }

    private func makeProcess(
        executable: URL,
        arguments: [String],
        directory: URL,
        environment extra: [String: String]
    ) -> Process {
        let process = Process()
        process.executableURL = executable
        process.arguments = arguments
        process.currentDirectoryURL = directory
        var environment = ProcessInfo.processInfo.environment
        let localBin = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".local/bin").path
        environment["PATH"] =
            "\(localBin):/opt/homebrew/bin:/usr/local/bin:" +
            "/usr/bin:/bin:/usr/sbin:/sbin"
        extra.forEach { environment[$0.key] = $0.value }
        process.environment = environment
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        return process
    }

    private func waitFor(_ address: String, seconds: Int) -> Bool {
        for _ in 0..<(seconds * 2) {
            let semaphore = DispatchSemaphore(value: 0)
            var success = false
            URLSession.shared.dataTask(with: URL(string: address)!) {
                _, response, _ in
                success = (response as? HTTPURLResponse)?.statusCode == 200
                semaphore.signal()
            }.resume()
            _ = semaphore.wait(timeout: .now() + 1)
            if success { return true }
            Thread.sleep(forTimeInterval: 0.5)
        }
        return false
    }

    private func setStatus(_ value: String) {
        DispatchQueue.main.async { self.status.stringValue = value }
    }

    private func markStep(_ index: Int) {
        DispatchQueue.main.async {
            let text = self.steps[index].stringValue.dropFirst(3)
            self.steps[index].stringValue = "✓  \(text)"
            self.steps[index].textColor = .systemGreen
        }
    }

    private func resetSteps() {
        for (index, label) in steps.enumerated() {
            let names = [
                "1. Verificar componentes",
                "2. Iniciar Granite local",
                "3. Iniciar sistema de suporte",
                "4. Publicar link temporário",
            ]
            label.stringValue = "○  \(names[index])"
            label.textColor = muted
        }
    }

    private func fail(_ message: String) {
        DispatchQueue.main.async {
            self.stopAll()
            self.status.stringValue = message
            self.progress.stopAnimation(nil)
            self.progress.isHidden = true
            self.start.isEnabled = true
            self.accessPassword.isEnabled = true
        }
    }

    @objc private func copyPublicLink() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(publicURL, forType: .string)
    }

    @objc private func openPublicLink() {
        if let url = URL(string: publicURL) {
            NSWorkspace.shared.open(url)
        }
    }

    @objc private func stopAndReset() {
        stopAll()
        publicURL = ""
        status.stringValue = "Pronto para iniciar"
        link.stringValue = "O link aparecerá aqui"
        styleButton(
            start,
            title: "Ligar OSS",
            background: ink,
            foreground: .white
        )
        start.isEnabled = true
        accessPassword.isEnabled = true
        [copyLink, openLink, stop].forEach { $0.isEnabled = false }
        resetSteps()
    }

    private func stopAll() {
        processes.reversed().forEach { process in
            if process.isRunning {
                terminateTree(process.processIdentifier)
                process.terminate()
            }
        }
        processes.removeAll()
        ollamaStartedHere = false
        try? FileManager.default.removeItem(
            at: root.appendingPathComponent(".oss-session-url")
        )
    }

    private func terminateTree(_ pid: Int32) {
        let lookup = Process()
        let output = Pipe()
        lookup.executableURL = URL(fileURLWithPath: "/usr/bin/pgrep")
        lookup.arguments = ["-P", String(pid)]
        lookup.standardOutput = output
        try? lookup.run()
        lookup.waitUntilExit()
        let data = output.fileHandleForReading.readDataToEndOfFile()
        let children = (String(data: data, encoding: .utf8) ?? "")
            .split(separator: "\n")
            .compactMap { Int32($0) }
        children.forEach { terminateTree($0) }
        Darwin.kill(pid, SIGTERM)
    }

    private func makeIcon(size: CGFloat) -> NSImage {
        let image = NSImage(size: NSSize(width: size, height: size))
        image.lockFocus()
        NSColor(
            calibratedRed: 0.02,
            green: 0.13,
            blue: 0.18,
            alpha: 1
        ).setFill()
        NSBezierPath(
            roundedRect: NSRect(x: 0, y: 0, width: size, height: size),
            xRadius: size * 0.18,
            yRadius: size * 0.18
        ).fill()
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: size * 0.30, weight: .bold),
            .foregroundColor: NSColor.white,
        ]
        let text = NSAttributedString(string: "OSS", attributes: attributes)
        let textSize = text.size()
        text.draw(
            at: NSPoint(
                x: (size - textSize.width) / 2,
                y: (size - textSize.height) / 2
            )
        )
        image.unlockFocus()
        return image
    }
}

let application = NSApplication.shared
let delegate = OSSLauncher()
application.delegate = delegate
application.setActivationPolicy(.regular)
application.run()
