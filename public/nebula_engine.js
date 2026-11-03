/**
 * ==============================================================================
 * 🌌 NEBULA ENGINE — 3D Volumetric Synaptic Substrate & Plasma Memory Universe
 * Pure WebGL (Three.js + OrbitControls) with Zero External Dependencies.
 *
 * Architecture:
 * 1. Volumetric Cosmic Nebula with 3,500+ harmonic stardust particles.
 * 2. 5 Hyperfocused 3D Galaxy Clusters:
 *    - Agents Galaxy (Antigravity, Grok, Claude, Hermes, Cursor, Sentinel, Ollama)
 *    - Tools Galaxy (Bash CLI, AST parser, Math pillar, Code tools)
 *    - Security Galaxy (Guardrails, Sandboxes, Entropy, Crypto, Auth)
 *    - System Galaxy (Kernel, SQLite WAL, Telemetry, Memory substrate)
 *    - Living Minds Galaxy (Civilization colonies, Emergent dialogues)
 * 3. Curved Bezier Synaptic Filaments with STDP plastic weight modulation.
 * 4. "Plasma Liquid Air" Action Potential Pulses flowing along biological axons.
 * 5. Real-time Live Brain Triggers via SSE /api/stream and interactive firing.
 * ==============================================================================
 */

(function () {
  'use strict';

  // Galaxy Cluster Coordinate Offsets and Color Palette
  const GALAXY_CLUSTERS = {
    agents: {
      name: 'Agents Galaxy',
      id: 'agents',
      center: new THREE.Vector3(-220, 60, -80),
      color: 0xD4AF37, // Sovereign Gold
      hex: '#D4AF37',
      auraColor: 0xF5E6AB,
      description: 'Antigravity, Grok, Claude, Hermes, Cursor, Sentinel, Ollama',
    },
    tools: {
      name: 'Tools Galaxy',
      id: 'tools',
      center: new THREE.Vector3(220, 80, -100),
      color: 0x00E5FF, // Electric Cyan
      hex: '#00E5FF',
      auraColor: 0x80F0FF,
      description: 'Bash CLI, AST Parser, Network, Math Pillar, Python Tools',
    },
    security: {
      name: 'Security Galaxy',
      id: 'security',
      center: new THREE.Vector3(180, -120, 140),
      color: 0xFF3366, // Crimson Laser
      hex: '#FF3366',
      auraColor: 0xFF809B,
      description: 'Memory Guardrails, Sandboxes, Entropy, Zero-Egress, Crypto',
    },
    system: {
      name: 'System Galaxy',
      id: 'system',
      center: new THREE.Vector3(-180, -130, 100),
      color: 0xA855F7, // Deep Violet
      hex: '#A855F7',
      auraColor: 0xD8B4FE,
      description: 'ZothOS Kernel, SQLite WAL, Process Tree, Hardware Telemetry',
    },
      living_minds: {
        name: 'Living Minds Galaxy',
        id: 'living_minds',
        center: new THREE.Vector3(0, 160, 80),
        color: 0x10B981, // Emerald Biome
        hex: '#10B981',
        auraColor: 0x6EE7B7,
        description: 'Civilization Colonies, Epistemic Reflections, Autonomous Mind',
      },
      obsidian: {
        name: 'Obsidian Second Brain',
        id: 'obsidian',
        center: new THREE.Vector3(0, -145, 165),
        color: 0xE879F9, // Radiant Fuchsia-Amethyst
        hex: '#E879F9',
        auraColor: 0xF5D0FE,
        description: 'Obsidian Vault MOCs, JSON Canvas (.canvas), Bases (.base) & 7 Agent Skills',
      },
    };

  // 5 Neuromodulatory Neurochemical States & Plasticity Presets
  const NEUROMODULATOR_MODES = {
    balanced: {
      id: 'balanced',
      name: 'Balanced',
      label: '🌌 Balanced',
      colorHex: '#D4AF37',
      colorNum: 0xD4AF37,
      secondaryHex: '#00E5FF',
      secondaryNum: 0x00E5FF,
      speedMultiplier: 1.0,
      rotationMultiplier: 1.0,
      coreEmissiveIntensity: 0.85,
      coreScaleMultiplier: 1.0,
      filamentOpacity: 0.35,
      pulseFrequency: 1.2,
      desc: 'Gold/Cyan equilibrium, normal 1.0x synaptic speed, baseline STDP plasticity.',
    },
    dopamine: {
      id: 'dopamine',
      name: 'Dopamine Reward',
      label: '⚡ Dopamine Reward',
      colorHex: '#f59e0b',
      colorNum: 0xF59E0B,
      secondaryHex: '#fbbf24',
      secondaryNum: 0xFBBF24,
      speedMultiplier: 2.2,
      rotationMultiplier: 1.8,
      coreEmissiveIntensity: 1.6,
      coreScaleMultiplier: 1.35,
      filamentOpacity: 0.7,
      pulseFrequency: 4.8,
      desc: 'Radiant Gold, 2.2x synaptic pulse speed, expanded core glow & reward plasticity surge.',
    },
    norepinephrine: {
      id: 'norepinephrine',
      name: 'Norepinephrine Alert',
      label: '🔥 Norepinephrine Alert',
      colorHex: '#f43f5e',
      colorNum: 0xF43F5E,
      secondaryHex: '#fb923c',
      secondaryNum: 0xFB923C,
      speedMultiplier: 2.8,
      rotationMultiplier: 3.0,
      coreEmissiveIntensity: 1.9,
      coreScaleMultiplier: 1.2,
      filamentOpacity: 0.75,
      pulseFrequency: 6.5,
      desc: 'Crimson/Orange, 3.0x rapid-fire cortical rotation & shockwaves, high-salience vigilance.',
    },
    acetylcholine: {
      id: 'acetylcholine',
      name: 'Acetylcholine Focus',
      label: '🌊 Acetylcholine Focus',
      colorHex: '#06b6d4',
      colorNum: 0x06B6D4,
      secondaryHex: '#38bdf8',
      secondaryNum: 0x38BDF8,
      speedMultiplier: 1.4,
      rotationMultiplier: 1.2,
      coreEmissiveIntensity: 1.3,
      coreScaleMultiplier: 1.1,
      filamentOpacity: 0.85,
      pulseFrequency: 2.6,
      desc: 'Electric Cyan, sharpened filament opacity, deep encoding beam lock.',
    },
    serotonin: {
      id: 'serotonin',
      name: 'Serotonin Consolidation',
      label: '💜 Serotonin Consolidation',
      colorHex: '#a855f7',
      colorNum: 0xA855F7,
      secondaryHex: '#c084fc',
      secondaryNum: 0xC084FC,
      speedMultiplier: 0.6,
      rotationMultiplier: 0.5,
      coreEmissiveIntensity: 1.0,
      coreScaleMultiplier: 1.05,
      filamentOpacity: 0.45,
      pulseFrequency: 0.8,
      desc: 'Deep Violet, slow 0.6x harmonic consolidation waves & dream-replay ripples.',
    },
  };

  // Helper to generate soft radial glow particle sprite in-memory (no external image assets)
  function createGlowTexture(colorStr, radius = 64) {
    const canvas = document.createElement('canvas');
    canvas.width = radius * 2;
    canvas.height = radius * 2;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius);
    grad.addColorStop(0, colorStr || '#ffffff');
    grad.addColorStop(0.2, colorStr || '#ffffff');
    grad.addColorStop(0.6, 'rgba(255,255,255,0.2)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, radius * 2, radius * 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  // Text billboard sprite generator for floating 3D labels
  function createTextSprite(text, colorStr = '#D4AF37', fontSize = 28) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, 512, 128);
    ctx.font = `bold ${fontSize}px "Google Sans", "Segoe UI", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Text shadow for high contrast over nebula
    ctx.shadowColor = 'rgba(0, 0, 0, 0.9)';
    ctx.shadowBlur = 10;
    ctx.fillStyle = colorStr;
    ctx.fillText(text, 256, 64);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(60, 15, 1);
    return sprite;
  }

  // HTML escaping utility for safe HUD text injection
  function escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Pure Web Audio API Synthesizer for Bio-Resonant Synaptic Feedback (Zero Files/CDNs)
  class BioAudioSynthesizer {
    constructor() {
      this.ctx = null;
      this.enabled = false;
    }

    ensureContext() {
      if (!this.ctx && typeof (window.AudioContext || window.webkitAudioContext) !== 'undefined') {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioCtx();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
    }

    playActionPotential(freq = 528) {
      if (!this.enabled) return;
      try {
        this.ensureContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq * 0.85, now);
        osc.frequency.exponentialRampToValueAtTime(freq * 1.3, now + 0.08);

        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.18);
      } catch (e) {}
    }

    playSleepRipple() {
      if (!this.enabled) return;
      try {
        this.ensureContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [432, 528, 648].forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, now + idx * 0.1);

          gain.gain.setValueAtTime(0.035, now + idx * 0.1);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.1 + 0.8);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(now + idx * 0.1);
          osc.stop(now + idx * 0.1 + 0.85);
        });
      } catch (e) {}
    }

    playHarmonicChord(baseFreq = 528) {
      if (!this.enabled) return;
      try {
        this.ensureContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const freqs = [baseFreq, baseFreq * 1.25, baseFreq * 1.5];
        freqs.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, now + idx * 0.04);
          gain.gain.setValueAtTime(0.04, now + idx * 0.04);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.04 + 0.6);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.04);
          osc.stop(now + idx * 0.04 + 0.65);
        });
      } catch (e) {}
    }

    toggle() {
      this.enabled = !this.enabled;
      if (this.enabled) this.ensureContext();
      return this.enabled;
    }
  }

  class NebulaUniverse {
    constructor(containerElement) {
      this.container = containerElement;
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();

      this.audio = new BioAudioSynthesizer();
      this.pointerDownPos = { x: 0, y: 0 };
      this.pointerDownTime = 0;

      this.stardustPoints = null;
      this.stardustPositions = null;
      this.galaxyCores = [];
      this.nodeMeshes = new Map(); // id -> THREE.Mesh
      this.filamentCurves = []; // list of { curve, line, sourceId, targetId, weight }
      this.plasmaPulses = []; // active traveling action potentials

      this.cameraTarget = new THREE.Vector3(0, 0, 0);
      this.cameraLookAt = new THREE.Vector3(0, 0, 0);
      this.isGlidingCamera = false;
      this.glideDuration = 1.4;
      this.glideStartTime = 0;
      this.glideStartPos = new THREE.Vector3();
      this.glideEndPos = new THREE.Vector3();
      this.glideStartLook = new THREE.Vector3();
      this.glideEndLook = new THREE.Vector3();

      this.isTouring = false;
      this.tourStep = 0;
      this.tourTimer = null;
      this.pathwayBannerTimer = null;
      this.birthBannerTimer = null;
      this.activePathway = null;
      this.currentNeuromodulator = 'balanced';
      this.neuromodulatorState = NEUROMODULATOR_MODES.balanced;
      this.trailingSparkles = [];
      this.salienceThreshold = 0.0;
      this.isDreaming = false;
      this.dreamWaveTimer = null;
      this.dreamWaveGroup = null;

      this.tourStops = [
        {
          id: 'agents',
          name: 'Agents Galaxy',
          icon: '◈',
          hex: '#D4AF37',
          color: 0xD4AF37,
          camPos: new THREE.Vector3(-160, 95, 60),
          lookAt: new THREE.Vector3(-220, 60, -80),
          narration: 'Autonomous LLM cognitive runtimes: Antigravity, Grok, Claude, Hermes, and Sentinel. Orchestrates multi-agent memory synthesis and sovereign epistemic consensus.',
          telemetry: 'Plasticity: 3-Factor STDP • Synaptic Potentiation: Active',
        },
        {
          id: 'tools',
          name: 'Tools Galaxy',
          icon: '⚙️',
          hex: '#00E5FF',
          color: 0x00E5FF,
          camPos: new THREE.Vector3(270, 115, 45),
          lookAt: new THREE.Vector3(220, 80, -100),
          narration: 'Procedural memory substrate & tool procedures: Bash CLI, AST parsing, math synthesis, and automated code analysis routines.',
          telemetry: 'Procedural Cache: Zero-Latency • Hot Synapses: Online',
        },
        {
          id: 'security',
          name: 'Security Galaxy',
          icon: '❖',
          hex: '#FF3366',
          color: 0xFF3366,
          camPos: new THREE.Vector3(230, -90, 280),
          lookAt: new THREE.Vector3(180, -120, 140),
          narration: 'Cryptographic memory boundaries, zero-egress sandboxes, entropy monitors, credential scrubbing, and adversarial guardrail engrams.',
          telemetry: 'Memory Isolation: Enforced • Leak Protection: 100%',
        },
        {
          id: 'system',
          name: 'System Galaxy',
          icon: '▣',
          hex: '#A855F7',
          color: 0xA855F7,
          camPos: new THREE.Vector3(-135, -95, 240),
          lookAt: new THREE.Vector3(-180, -130, 100),
          narration: 'ZothOS Substrate Engine: SQLite WAL persistence, process hierarchies, hardware thermals (<60°C target), and kernel telemetry.',
          telemetry: 'Storage: SQLite WAL • Substrate Status: Pristine',
        },
        {
          id: 'living_minds',
          name: 'Living Minds Galaxy',
          icon: '◈',
          hex: '#10B981',
          color: 0x10B981,
          camPos: new THREE.Vector3(45, 195, 220),
          lookAt: new THREE.Vector3(0, 160, 80),
          narration: 'Civilization colonies, epistemic self-reflections, emergent dialogues, and autonomous cognitive evolution over deep time.',
          telemetry: 'Cognitive Emergence: High • Colony Cohesion: 98.4%',
        },
        {
          id: 'obsidian',
          name: 'Obsidian Second Brain',
          icon: '💎',
          hex: '#E879F9',
          color: 0xE879F9,
          camPos: new THREE.Vector3(45, -115, 300),
          lookAt: new THREE.Vector3(0, -145, 165),
          narration: 'Bidirectional Obsidian vault sync, JSON Canvas (.canvas), Obsidian Bases (.base), wikilinks, and sovereign MOC knowledge graphs.',
          telemetry: 'Second Brain Sync: Live • Vault Engrams: Bidirectional',
        },
        {
          id: 'core',
          name: 'Netrunner Cyber-Cortex',
          icon: '⚡',
          hex: '#00E5FF',
          color: 0x00E5FF,
          camPos: new THREE.Vector3(0, 35, 145),
          lookAt: new THREE.Vector3(0, -10, 0),
          narration: 'Central 3-Factor STDP Neural Cortex, articulated cybernetic spine, and global Hippocampal Sharp-Wave Ripple (SWR) generator.',
          telemetry: 'Frequency: 1.2–8.0 Hz • Plasticity: 3-Factor STDP',
        },
        {
          id: 'all',
          name: 'Panoramic Cosmic Universe',
          icon: '✦',
          hex: '#D4AF37',
          color: 0xD4AF37,
          camPos: new THREE.Vector3(0, 180, 520),
          lookAt: new THREE.Vector3(0, 0, 0),
          narration: 'Panoramic view of the complete 6-galaxy neural universe, curved Bezier synaptic filaments, and stardust cosmic halo.',
          telemetry: 'Total Universe Engaged • STDP Plasticity: Synchronized',
        },
      ];

      this.clock = new THREE.Clock();
      this.hoveredNode = null;
      this.selectedNode = null;
      this.sseSource = null;
      this.stats = {
        totalEngrams: 0,
        totalSynapses: 0,
        activePulses: 0,
        actionFrequency: 1.2,
      };

      this.onNodeClickCallback = null;
      this.onNodeHoverCallback = null;

      this.init();
    }

    init() {
      const width = this.container.clientWidth || 800;
      const height = this.container.clientHeight || 500;

      // 1. Scene & Background
      this.scene = new THREE.Scene();
      this.scene.fog = new THREE.FogExp2(0x08080B, 0.0012);

      // 2. Camera
      this.camera = new THREE.PerspectiveCamera(50, width / height, 1, 3000);
      this.camera.position.set(0, 180, 520);
      this.camera.lookAt(0, 0, 0);

      // 3. Renderer
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.setClearColor(0x08080B, 1);
      this.container.appendChild(this.renderer.domElement);
      this.renderer.domElement.id = 'nebula-3d-canvas';
      this.renderer.domElement.style.width = '100%';
      this.renderer.domElement.style.height = '100%';
      this.renderer.domElement.style.display = 'block';

      // 4. OrbitControls
      if (typeof THREE.OrbitControls === 'function') {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.rotateSpeed = 0.6;
        this.controls.zoomSpeed = 0.8;
        this.controls.maxDistance = 1200;
        this.controls.minDistance = 60;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 0.4;
      }

      // 5. Lights
      const ambientLight = new THREE.AmbientLight(0x222233, 1.2);
      this.scene.add(ambientLight);

      const centerLight = new THREE.PointLight(0xD4AF37, 2.0, 800);
      centerLight.position.set(0, 0, 0);
      this.scene.add(centerLight);

      const cyanFillLight = new THREE.PointLight(0x00E5FF, 1.5, 600);
      cyanFillLight.position.set(200, 100, 200);
      this.scene.add(cyanFillLight);

      const purpleFillLight = new THREE.PointLight(0x8A2BE2, 1.5, 600);
      purpleFillLight.position.set(-200, -100, -200);
      this.scene.add(purpleFillLight);

      // 6. Build Stardust, Galaxy Clusters & Interactive 3D Netrunner Core Model
      this.buildStardustField();
      this.buildGalaxyClusters();
      this.buildNetrunnerCoreModel();

      // 7. Event Listeners
      window.addEventListener('resize', () => this.onWindowResize());
      this.renderer.domElement.addEventListener('mousemove', (e) => this.onMouseMove(e));
      this.renderer.domElement.addEventListener('pointerdown', (e) => {
        this.pointerDownPos = { x: e.clientX, y: e.clientY };
        this.pointerDownTime = performance.now();
      });
      this.renderer.domElement.addEventListener('pointerup', (e) => {
        const dx = e.clientX - this.pointerDownPos.x;
        const dy = e.clientY - this.pointerDownPos.y;
        const dist = Math.hypot(dx, dy);
        const elapsed = performance.now() - this.pointerDownTime;
        if (dist < 8 && elapsed < 500) {
          this.handleNodeClick(e);
        }
      });

      // 8. Animation Loop
      this.animate();

      // 9. Wire SSE Stream
      this.connectSSE();
    }

    buildStardustField() {
      const particleCount = 3800;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);
      const sizes = new Float32Array(particleCount);

      const palette = [
        new THREE.Color(0xD4AF37), // Gold
        new THREE.Color(0xF5E6AB), // Pale Gold
        new THREE.Color(0x00E5FF), // Cyan
        new THREE.Color(0x8A2BE2), // Violet
        new THREE.Color(0x10B981), // Emerald
        new THREE.Color(0x4A6CF7), // Royal Blue
      ];

      for (let i = 0; i < particleCount; i++) {
        // Spherical distribution with denser inner cosmic halo
        const radius = Math.pow(Math.random(), 0.7) * 700;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);

        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = (radius * Math.sin(phi) * Math.sin(theta)) * 0.65; // flattened galactic disc
        const z = radius * Math.cos(phi);

        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;

        const col = palette[Math.floor(Math.random() * palette.length)];
        colors[i * 3] = col.r;
        colors[i * 3 + 1] = col.g;
        colors[i * 3 + 2] = col.b;

        sizes[i] = Math.random() * 3.5 + 1.2;
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

      this.stardustPositions = positions;

      const particleTexture = createGlowTexture('rgba(255,255,255,0.95)', 32);
      const material = new THREE.PointsMaterial({
        size: 3.5,
        map: particleTexture,
        vertexColors: true,
        transparent: true,
        opacity: 0.75,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      this.stardustPoints = new THREE.Points(geometry, material);
      this.scene.add(this.stardustPoints);
    }

    buildGalaxyClusters() {
      const coreTexture = createGlowTexture('rgba(255,255,255,1)', 64);

      Object.values(GALAXY_CLUSTERS).forEach((galaxy) => {
        // Glowing Core Sprite
        const mat = new THREE.SpriteMaterial({
          map: coreTexture,
          color: galaxy.color,
          transparent: true,
          opacity: 0.65,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const sprite = new THREE.Sprite(mat);
        sprite.position.copy(galaxy.center);
        sprite.scale.set(70, 70, 1);
        this.scene.add(sprite);

        // Core Halo ring
        const ringGeo = new THREE.RingGeometry(25, 27, 48);
        const ringMat = new THREE.MeshBasicMaterial({
          color: galaxy.color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.35,
          blending: THREE.AdditiveBlending,
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.copy(galaxy.center);
        ring.rotation.x = Math.PI / 2;
        this.scene.add(ring);

        // Floating 3D Title Label
        const titleSprite = createTextSprite(galaxy.name, galaxy.hex, 32);
        titleSprite.position.set(galaxy.center.x, galaxy.center.y + 40, galaxy.center.z);
        this.scene.add(titleSprite);

        this.galaxyCores.push({
          sprite,
          ring,
          title: titleSprite,
          galaxy,
        });
      });
    }

    buildNetrunnerCoreModel() {
      const coreGroup = new THREE.Group();
      coreGroup.position.set(0, 0, 0);

      // 1. Cybernetic Icosahedral Brain Cortex (Wireframe + Inner Emissive Core)
      const brainGeo = new THREE.IcosahedronGeometry(26, 2);
      const brainWireMat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        wireframe: true,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
      });
      const brainWireMesh = new THREE.Mesh(brainGeo, brainWireMat);
      coreGroup.add(brainWireMesh);

      const innerCoreGeo = new THREE.IcosahedronGeometry(14, 1);
      const innerCoreMat = new THREE.MeshStandardMaterial({
        color: 0xD4AF37,
        emissive: 0xD4AF37,
        emissiveIntensity: 0.85,
        roughness: 0.2,
        metalness: 0.9,
      });
      const innerCoreMesh = new THREE.Mesh(innerCoreGeo, innerCoreMat);
      innerCoreMesh.userData = {
        isNetrunnerCore: true,
        nodeData: {
          id: 'netrunner-core-0',
          label: 'NETRUNNER CYBER-CORTEX CORE',
          text: 'Sovereign 3-Factor STDP Neural Cortex & Obsidian Second Brain Bridge. Click to fire global Hippocampal Sharp-Wave Ripple (SWR) across all 6 galaxy clusters.',
          category: 'architecture',
          agent_id: 'azoth',
          importance: 2.0,
          access_count: 99,
          tags: ['netrunner', 'stdp', 'cortex', 'obsidian', 'hippocampus'],
        },
        galaxy: { name: 'Netrunner Cyber-Cortex', hex: '#D4AF37', color: 0xD4AF37 },
        baseColor: 0xD4AF37,
        baseRadius: 1.0,
      };
      coreGroup.add(innerCoreMesh);

      // 2. Glowing Cybernetic Optic Visor Arc
      const visorGeo = new THREE.TorusGeometry(28, 1.4, 12, 48, Math.PI * 0.85);
      const visorMat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const visorMesh = new THREE.Mesh(visorGeo, visorMat);
      visorMesh.rotation.x = Math.PI / 2;
      visorMesh.rotation.z = -Math.PI * 0.42;
      visorMesh.position.y = 4;
      coreGroup.add(visorMesh);

      // 3. Articulated Cybernetic Spinal Column (7 Cervical/Thoracic Neural Vertebrae)
      const spineGroup = new THREE.Group();
      for (let i = 0; i < 7; i++) {
        const radius = 8 - i * 0.7;
        const discGeo = new THREE.CylinderGeometry(radius, radius * 0.85, 3.2, 16);
        const discMat = new THREE.MeshStandardMaterial({
          color: i % 2 === 0 ? 0xD4AF37 : 0x00E5FF,
          emissive: i % 2 === 0 ? 0xD4AF37 : 0x00E5FF,
          emissiveIntensity: 0.5,
          metalness: 0.8,
          roughness: 0.3,
        });
        const disc = new THREE.Mesh(discGeo, discMat);
        disc.position.y = -32 - i * 7.5;
        spineGroup.add(disc);
      }
      coreGroup.add(spineGroup);

      // 4. Counter-Rotating Gyroscopic STDP Gimbal Rings
      const gimbal1Geo = new THREE.TorusGeometry(42, 0.65, 16, 96);
      const gimbal1Mat = new THREE.MeshBasicMaterial({
        color: 0xD4AF37,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
      });
      const gimbal1 = new THREE.Mesh(gimbal1Geo, gimbal1Mat);
      coreGroup.add(gimbal1);

      const gimbal2Geo = new THREE.TorusGeometry(52, 0.55, 16, 96);
      const gimbal2Mat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
      });
      const gimbal2 = new THREE.Mesh(gimbal2Geo, gimbal2Mat);
      gimbal2.rotation.x = Math.PI / 3;
      coreGroup.add(gimbal2);

      const gimbal3Geo = new THREE.TorusGeometry(62, 0.5, 16, 96);
      const gimbal3Mat = new THREE.MeshBasicMaterial({
        color: 0xE879F9,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
      });
      const gimbal3 = new THREE.Mesh(gimbal3Geo, gimbal3Mat);
      gimbal3.rotation.y = Math.PI / 4;
      coreGroup.add(gimbal3);

      // 5. Floating Label above the Netrunner Cyber-Cortex
      const coreLabel = createTextSprite('⚡ NETRUNNER CYBER-CORTEX', '#00E5FF', 28);
      coreLabel.position.set(0, 56, 0);
      coreGroup.add(coreLabel);

      this.scene.add(coreGroup);
      this.netrunnerCore = {
        group: coreGroup,
        brainWireMesh,
        innerCoreMesh,
        visorMesh,
        spineGroup,
        gimbal1,
        gimbal2,
        gimbal3,
      };
    }

    // Determine which 3D galaxy cluster an engram belongs to
    determineGalaxy(node) {
      const text = (node.label || node.text || '').toLowerCase();
      const cat = (node.category || '').toLowerCase();
      const tags = (node.tags || []).map(t => String(t).toLowerCase());
      const agentId = (node.agent_id || '').toLowerCase();

      // 0. Obsidian Second Brain Galaxy
      if (
        cat === 'obsidian' || cat === 'vault' || cat === 'second-brain' ||
        agentId.includes('obsidian') ||
        tags.some(t => ['obsidian', 'vault', 'moc', 'wikilink', 'canvas', 'json-canvas', 'obsidian-bases', 'second-brain', 'defuddle', 'knap'].includes(t)) ||
        text.includes('obsidian') || text.includes('[[') || text.includes('.canvas') || text.includes('.base') || text.includes('second brain')
      ) {
        return GALAXY_CLUSTERS.obsidian;
      }

      // 1. Agents Galaxy
      if (
        agentId.includes('antigravity') || agentId.includes('grok') || agentId.includes('claude') ||
        agentId.includes('hermes') || agentId.includes('cursor') || agentId.includes('sentinel') ||
        tags.some(t => ['agent', 'subagent', 'antigravity', 'grok', 'claude', 'hermes', 'llm', 'mcp'].includes(t)) ||
        text.includes('agent') || text.includes('grok') || text.includes('antigravity')
      ) {
        return GALAXY_CLUSTERS.agents;
      }

      // 2. Tools Galaxy
      if (
        cat === 'tool' || cat === 'procedure' ||
        tags.some(t => ['tool', 'bash', 'ast', 'git', 'cli', 'math', 'code', 'regex', 'curl', 'compiler'].includes(t)) ||
        text.includes('command') || text.includes('bash') || text.includes('script')
      ) {
        return GALAXY_CLUSTERS.tools;
      }

      // 3. Security Galaxy
      if (
        cat === 'security' ||
        tags.some(t => ['security', 'sandbox', 'entropy', 'auth', 'jwt', 'crypto', 'firewall', 'guardrail', 'egress'].includes(t)) ||
        text.includes('security') || text.includes('vulnerability') || text.includes('cipher')
      ) {
        return GALAXY_CLUSTERS.security;
      }

      // 4. System Galaxy
      if (
        cat === 'architecture' || cat === 'debug' ||
        tags.some(t => ['kernel', 'sqlite', 'wal', 'storage', 'process', 'hardware', 'daemon', 'system', 'zothos'].includes(t)) ||
        text.includes('kernel') || text.includes('database') || text.includes('systemd')
      ) {
        return GALAXY_CLUSTERS.system;
      }

      // 5. Living Minds Galaxy (Default for semantic, reflections, dialogues)
      return GALAXY_CLUSTERS.living_minds;
    }

    loadGraph(nodes, edges) {
      // Clear existing node meshes and filaments
      this.nodeMeshes.forEach(mesh => this.scene.remove(mesh));
      this.nodeMeshes.clear();

      this.filamentCurves.forEach(item => this.scene.remove(item.line));
      this.filamentCurves = [];

      this.plasmaPulses.forEach(pulse => {
        if (pulse.mesh) this.scene.remove(pulse.mesh);
      });
      this.plasmaPulses = [];

      this.stats.totalEngrams = nodes.length;
      this.stats.totalSynapses = edges.length;

      const sphereGeo = new THREE.SphereGeometry(1, 24, 24);

      // 1. Position and instantiate Node Meshes in 3D Galaxy Clusters
      nodes.forEach((node, idx) => {
        const galaxy = this.determineGalaxy(node);
        const clusterCenter = galaxy.center;

        // Pseudo-random deterministic spherical offset within galaxy cluster
        const seedVal = (idx + 1) * 9301 + 49297;
        const angle1 = (seedVal % 1000) / 1000 * Math.PI * 2;
        const angle2 = ((seedVal * 7) % 1000) / 1000 * Math.PI - (Math.PI / 2);
        const dist = 20 + (((seedVal * 13) % 1000) / 1000) * 85;

        const posX = clusterCenter.x + Math.cos(angle1) * Math.cos(angle2) * dist;
        const posY = clusterCenter.y + Math.sin(angle2) * (dist * 0.75);
        const posZ = clusterCenter.z + Math.sin(angle1) * Math.cos(angle2) * dist;

        // Node size based on importance and access count
        const importance = typeof node.importance === 'number' ? node.importance : 1.0;
        const accessCount = node.access_count || 1;
        const nodeRadius = Math.max(3.0, Math.min(10.0, (3.2 * importance) + Math.log1p(accessCount) * 0.8));

        const mat = new THREE.MeshStandardMaterial({
          color: galaxy.color,
          emissive: galaxy.color,
          emissiveIntensity: 0.55,
          roughness: 0.25,
          metalness: 0.8,
        });

        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.scale.set(nodeRadius, nodeRadius, nodeRadius);
        mesh.position.set(posX, posY, posZ);
        mesh.userData = {
          nodeData: node,
          galaxy: galaxy,
          baseColor: galaxy.color,
          baseRadius: nodeRadius,
          isPulsing: false,
        };

        this.scene.add(mesh);
        this.nodeMeshes.set(String(node.id), mesh);
      });

      // 1b. Ensure each of the 6 galaxies has at least one anchor star represented
      Object.keys(GALAXY_CLUSTERS).forEach((galaxyKey) => {
        const galaxy = GALAXY_CLUSTERS[galaxyKey];
        const hasNodes = Array.from(this.nodeMeshes.values()).some(m => m.userData && m.userData.galaxy && m.userData.galaxy.id === galaxy.id);
        if (!hasNodes) {
          const anchorData = {
            id: `anchor-${galaxy.id}`,
            label: `${galaxy.name} Core Star`,
            text: `${galaxy.name}: ${galaxy.description}. Sovereign STDP cluster.`,
            category: galaxy.id,
            tags: [galaxy.id, 'sovereign', 'nebula', 'stdp'],
            importance: 1.4,
            access_count: 5,
          };
          this.anchorNewEngramNode(anchorData, galaxy, galaxy.center.clone());
        }
      });

      // 2. Build Curved Bezier Synaptic Filaments
      const seenPairs = new Set();
      const filamentMatWeak = new THREE.LineBasicMaterial({
        color: 0x4A6CF7,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
      });
      const filamentMatMed = new THREE.LineBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
      });
      const filamentMatStrong = new THREE.LineBasicMaterial({
        color: 0xFFD700,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });

      edges.forEach((edge) => {
        const srcMesh = this.nodeMeshes.get(String(edge.source));
        const tgtMesh = this.nodeMeshes.get(String(edge.target));
        if (!srcMesh || !tgtMesh) return;

        const pairKey = [String(edge.source), String(edge.target)].sort().join('<->');
        if (seenPairs.has(pairKey)) return;
        seenPairs.add(pairKey);

        const p1 = srcMesh.position;
        const p2 = tgtMesh.position;

        // Quadratic Bezier midpoint arched outward
        const midPoint = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const dist = p1.distanceTo(p2);
        const arcHeight = Math.min(60, dist * 0.25);
        midPoint.y += arcHeight; // lift upward

        const curve = new THREE.QuadraticBezierCurve3(p1, midPoint, p2);
        const points = curve.getPoints(24);
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);

        const weight = typeof edge.weight === 'number' ? edge.weight : 0.2;
        let lineMat = filamentMatWeak;
        if (weight >= 0.6) lineMat = filamentMatStrong;
        else if (weight >= 0.3) lineMat = filamentMatMed;

        const line = new THREE.Line(lineGeo, lineMat);
        this.scene.add(line);

        this.filamentCurves.push({
          curve,
          line,
          sourceId: String(edge.source),
          targetId: String(edge.target),
          weight,
          srcPos: p1,
          tgtPos: p2,
        });

        // Spawn ambient plasma action potential pulses along strong synapses
        if (weight >= 0.4 || Math.random() < 0.25) {
          this.spawnPlasmaPulse(curve, weight, lineMat.color);
        }
      });

      this.updateHudStats();
    }

    spawnPlasmaPulse(curve, weight = 0.5, color = 0xFFD700, speedMultiplier = 1.0) {
      const pulseGeo = new THREE.SphereGeometry(1.4, 12, 12);
      const pulseMat = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const mesh = new THREE.Mesh(pulseGeo, pulseMat);

      const pulse = {
        curve,
        mesh,
        t: Math.random(),
        speed: (0.12 + (weight * 0.18)) * speedMultiplier,
        size: 1.4 + (weight * 1.6),
      };
      mesh.scale.set(pulse.size, pulse.size, pulse.size);
      this.scene.add(mesh);
      this.plasmaPulses.push(pulse);
    }

    // High-speed one-shot plasma burst traveling along a synaptic pathway
    spawnPathwayBurst(curve, color = 0xFFD700, speedMultiplier = 2.4) {
      const pulseGeo = new THREE.SphereGeometry(2.2, 16, 16);
      const pulseMat = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending,
      });
      const mesh = new THREE.Mesh(pulseGeo, pulseMat);
      mesh.scale.set(1.6, 1.6, 1.6);

      const pulse = {
        curve,
        mesh,
        t: 0.0,
        speed: 0.36 * speedMultiplier,
        isOneShot: true,
      };
      this.scene.add(mesh);
      this.plasmaPulses.push(pulse);
    }

    // Trigger explosive action potential cascade across the neural network
    triggerCascade(cascadeData) {
      if (!cascadeData) return;

      const seedId = String(cascadeData.seed || '');
      const seedMesh = this.nodeMeshes.get(seedId);

      // Bio-resonant audio feedback
      if (this.audio) this.audio.playActionPotential(528);

      // 1. Shockwave ring at origin seed
      if (seedMesh) {
        this.fireShockwave(seedMesh.position, 0xFFD700, 2.2);
        this.flashNode(seedMesh, 0xFFFFFF, 1.8);
      }

      // 2. Staggered sequence firing
      const sequence = cascadeData.cascade_sequence || [];
      sequence.forEach((step, index) => {
        const delayMs = index * 120; // 120ms transmission latency per hop
        setTimeout(() => {
          const srcId = String(step.source || '').replace('tag_', '').replace('mem_', '');
          const tgtId = String(step.target || '').replace('tag_', '').replace('mem_', '');

          const srcMesh = this.nodeMeshes.get(srcId) || this.findMeshByTag(srcId);
          const tgtMesh = this.nodeMeshes.get(tgtId) || this.findMeshByTag(tgtId);

          if (srcMesh && tgtMesh) {
            // High-speed plasma pulse firing
            const mid = new THREE.Vector3().addVectors(srcMesh.position, tgtMesh.position).multiplyScalar(0.5);
            mid.y += 20;
            const curve = new THREE.QuadraticBezierCurve3(srcMesh.position, mid, tgtMesh.position);

            this.spawnPlasmaPulse(curve, 0.9, 0xFFFFFF, 2.5);
            this.flashNode(tgtMesh, 0x00E5FF, 1.5);
          }
        }, delayMs);
      });

      this.stats.actionFrequency = Math.min(8.0, this.stats.actionFrequency + 0.6);
      this.updateHudStats();
    }

    findMeshByTag(tagClean) {
      const lower = tagClean.toLowerCase();
      for (const mesh of this.nodeMeshes.values()) {
        const tags = (mesh.userData.nodeData.tags || []).map(t => String(t).toLowerCase());
        if (tags.includes(lower)) return mesh;
      }
      return null;
    }

    // Concentric counter-rotating coronal shockwave rings
    fireShockwave(centerPos, color = 0xD4AF37, scaleRate = 1.8) {
      const ringGeo = new THREE.RingGeometry(2, 4.5, 36);
      const ringMat = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(centerPos);
      ring.rotation.x = Math.PI / 2;
      this.scene.add(ring);

      const ringGeo2 = new THREE.RingGeometry(1.5, 3, 28);
      const ringMat2 = new THREE.MeshBasicMaterial({
        color: 0xFFFFFF,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending,
      });
      const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
      ring2.position.copy(centerPos);
      ring2.rotation.x = Math.PI / 2;
      this.scene.add(ring2);

      let scale = 1.0;
      let opacity = 0.9;
      const expandInterval = setInterval(() => {
        scale += scaleRate;
        opacity -= 0.045;
        ring.scale.set(scale, scale, 1);
        ring2.scale.set(scale * 0.75, scale * 0.75, 1);
        ring.rotation.z += 0.05;
        ring2.rotation.z -= 0.05;
        ringMat.opacity = Math.max(0, opacity);
        ringMat2.opacity = Math.max(0, opacity * 0.75);

        if (opacity <= 0) {
          clearInterval(expandInterval);
          this.scene.remove(ring);
          this.scene.remove(ring2);
          ringGeo.dispose();
          ringMat.dispose();
          ringGeo2.dispose();
          ringMat2.dispose();
        }
      }, 16);
    }

    flashNode(mesh, flashColor = 0xFFFFFF, scaleMultiplier = 1.6) {
      if (!mesh || mesh.userData.isPulsing) return;
      mesh.userData.isPulsing = true;

      const baseRadius = mesh.userData.baseRadius;

      mesh.material.emissive.setHex(flashColor);
      mesh.material.emissiveIntensity = 2.2;
      mesh.scale.set(baseRadius * scaleMultiplier, baseRadius * scaleMultiplier, baseRadius * scaleMultiplier);

      setTimeout(() => {
        mesh.material.emissive.setHex(mesh.userData.baseColor);
        mesh.material.emissiveIntensity = 0.55;
        mesh.scale.set(baseRadius, baseRadius, baseRadius);
        mesh.userData.isPulsing = false;
      }, 450);
    }

    // Smoothly spotlights and glides camera to an engram node, highlighting its synaptic neighborhood
    focusNode(nodeId) {
      const mesh = this.nodeMeshes.get(String(nodeId));
      if (!mesh) return;

      this.selectedNode = mesh;
      this.flashNode(mesh, 0xFFD700, 2.0);
      this.fireShockwave(mesh.position, 0xFFD700, 2.0);
      if (this.audio) this.audio.playActionPotential(660);

      const targetPos = new THREE.Vector3(
        mesh.position.x + 35,
        mesh.position.y + 20,
        mesh.position.z + 65
      );
      this.glideCameraTo(targetPos, mesh.position);

      const connectedIds = new Set();
      this.filamentCurves.forEach(item => {
        if (item.sourceId === String(nodeId) || item.targetId === String(nodeId)) {
          connectedIds.add(item.sourceId === String(nodeId) ? item.targetId : item.sourceId);
          item.line.material.opacity = 1.0;
          item.line.material.color.setHex(0xFFD700);
          this.spawnPlasmaPulse(item.curve, 0.9, 0xFFFFFF, 3.0);
        } else {
          item.line.material.opacity = 0.12;
        }
      });

      connectedIds.forEach(id => {
        const neighbor = this.nodeMeshes.get(id);
        if (neighbor && !neighbor.userData.isPulsing) {
          neighbor.material.emissiveIntensity = 1.2;
        }
      });
    }

    clearHighlights() {
      this.activePathway = null;
      this.filamentCurves.forEach(item => {
        const weight = item.weight || 0.2;
        if (weight >= 0.6) {
          item.line.material.opacity = 0.9;
          item.line.material.color.setHex(0xFFD700);
        } else if (weight >= 0.3) {
          item.line.material.opacity = 0.65;
          item.line.material.color.setHex(0x00E5FF);
        } else {
          item.line.material.opacity = 0.35;
          item.line.material.color.setHex(0x4A6CF7);
        }
      });

      this.nodeMeshes.forEach(mesh => {
        if (!mesh.userData.isPulsing) {
          mesh.material.emissiveIntensity = 0.55;
        }
      });

      const pathBanner = document.getElementById('nebula-pathway-banner');
      if (pathBanner) pathBanner.classList.remove('visible');
    }

    // Hippocampal Sleep Replay (Sharp-Wave Ripples & Consolidation Simulation)
    triggerSleepReplayCascade(report = {}) {
      if (this.audio) this.audio.playSleepRipple();

      // 1. Panoramic overview glide
      this.glideCameraTo(new THREE.Vector3(0, 220, 580), new THREE.Vector3(0, 0, 0));

      // 2. Sequential Hippocampal Sharp-Wave Ripples (SWRs) expanding radially from core
      const rippleColors = [0xFFD700, 0xA855F7, 0x00E5FF];
      rippleColors.forEach((col, idx) => {
        setTimeout(() => {
          this.fireShockwave(new THREE.Vector3(0, 0, 0), col, 3.2);
        }, idx * 260);
      });

      // 3. Stardust harmonic swirl
      if (this.stardustPoints && this.stardustPoints.material) {
        this.stardustPoints.material.opacity = 1.0;
        setTimeout(() => {
          this.stardustPoints.material.opacity = 0.75;
        }, 2800);
      }

      // 4. Wave of engram rehearsal & consolidation
      const allMeshes = Array.from(this.nodeMeshes.values());
      allMeshes.forEach((mesh, idx) => {
        const delay = 400 + (idx % 8) * 140;
        setTimeout(() => {
          this.flashNode(mesh, 0xFFD700, 1.8);
          this.filamentCurves.filter(f => f.sourceId === String(mesh.userData.nodeData.id)).forEach(f => {
            this.spawnPlasmaPulse(f.curve, 0.85, 0xFFD700, 2.2);
          });
        }, delay);
      });

      // 5. Pruning dissolution (if low-retention nodes exist)
      const prunedIds = report.pruned_ids || [];
      prunedIds.forEach(id => {
        const mesh = this.nodeMeshes.get(String(id));
        if (mesh) {
          this.dissolveNode(mesh);
        }
      });

      // 6. Display HUD sleep banner
      this.showSleepReplayBanner(report);
    }

    // Dissolve pruned memory engram into fading cosmic dust
    dissolveNode(mesh) {
      const pCount = 24;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(pCount * 3);
      const velocities = [];

      for (let i = 0; i < pCount; i++) {
        positions[i * 3] = mesh.position.x;
        positions[i * 3 + 1] = mesh.position.y;
        positions[i * 3 + 2] = mesh.position.z;
        velocities.push(new THREE.Vector3(
          (Math.random() - 0.5) * 1.8,
          (Math.random() - 0.5) * 1.8,
          (Math.random() - 0.5) * 1.8
        ));
      }
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const mat = new THREE.PointsMaterial({
        color: 0x9AA0A6,
        size: 2.5,
        transparent: true,
        opacity: 0.8,
      });
      const points = new THREE.Points(geo, mat);
      this.scene.add(points);

      let step = 0;
      const anim = setInterval(() => {
        step++;
        const pos = geo.attributes.position.array;
        for (let i = 0; i < pCount; i++) {
          pos[i * 3] += velocities[i].x;
          pos[i * 3 + 1] += velocities[i].y;
          pos[i * 3 + 2] += velocities[i].z;
        }
        geo.attributes.position.needsUpdate = true;
        mat.opacity -= 0.04;
        if (step >= 20 || mat.opacity <= 0) {
          clearInterval(anim);
          this.scene.remove(points);
          geo.dispose();
          mat.dispose();
        }
      }, 30);

      this.scene.remove(mesh);
      this.nodeMeshes.delete(String(mesh.userData.nodeData.id));
    }

    showSleepReplayBanner(report) {
      let banner = document.getElementById('nebula-sleep-banner');
      if (!banner) return;
      const reinforced = report.reinforced_synapses ?? report.rehearsed_count ?? report.reinforced ?? 8;
      const schemata = report.schemata_synthesized ?? 2;
      const pruned = report.pruned_count ?? 0;

      banner.innerHTML = `
        <div style="font-size:24px;">🌙</div>
        <div style="display:flex; flex-direction:column; gap:2px;">
          <div style="font-weight:700; font-size:12px; color:#FFD700; letter-spacing:0.5px;">HIPPOCAMPAL SLEEP REPLAY COMPLETE</div>
          <div style="font-size:11px; color:#EDEFF2;">Sharp-Wave Ripples (210 Hz) &bull; ${reinforced} Synapses Reinforced &bull; ${schemata} Schemata Synthesized &bull; ${pruned} Pruned</div>
        </div>
      `;
      banner.classList.add('visible');
      setTimeout(() => {
        banner.classList.remove('visible');
      }, 4800);
    }

    focusGalaxy(galaxyId, fromTour = false) {
      if (this.isTouring && !fromTour) {
        this.stopTour();
      }
      if (galaxyId === 'core' || galaxyId === 'netrunner') {
        this.clearHighlights();
        this.fireShockwave(new THREE.Vector3(0, 0, 0), 0x00E5FF, 2.4);
        if (this.audio) this.audio.playActionPotential(640);
        this.glideCameraTo(new THREE.Vector3(0, 35, 145), new THREE.Vector3(0, -10, 0));
        return;
      }

      const galaxy = GALAXY_CLUSTERS[galaxyId];
      if (!galaxy) {
        // Reset to panoramic cosmic view
        this.clearHighlights();
        this.glideCameraTo(new THREE.Vector3(0, 180, 520), new THREE.Vector3(0, 0, 0));
        return;
      }

      this.clearHighlights();
      const targetPos = new THREE.Vector3(
        galaxy.center.x + 60,
        galaxy.center.y + 40,
        galaxy.center.z + 160
      );
      this.glideCameraTo(targetPos, galaxy.center);
    }

    glideCameraTo(endPos, endLook, duration = 1.4) {
      this.glideStartPos.copy(this.camera.position);
      this.glideEndPos.copy(endPos);
      this.glideStartLook.copy(this.controls ? this.controls.target : new THREE.Vector3());
      this.glideEndLook.copy(endLook);
      this.glideStartTime = this.clock.getElapsedTime();
      this.glideDuration = duration;
      this.isGlidingCamera = true;
      if (this.controls) this.controls.autoRotate = false;
    }

    onWindowResize() {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }

    onMouseMove(event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.camera);
      const meshes = Array.from(this.nodeMeshes.values());
      if (this.netrunnerCore && this.netrunnerCore.innerCoreMesh) {
        meshes.push(this.netrunnerCore.innerCoreMesh);
      }
      const intersects = this.raycaster.intersectObjects(meshes);

      const tooltip = document.getElementById('nebula-hover-tooltip');

      if (intersects.length > 0) {
        const hitMesh = intersects[0].object;
        if (this.hoveredNode !== hitMesh) {
          if (this.hoveredNode && !this.hoveredNode.userData.isPulsing) {
            this.hoveredNode.material.emissiveIntensity = 0.55;
          }
          this.hoveredNode = hitMesh;
          this.hoveredNode.material.emissiveIntensity = 1.6;
          this.renderer.domElement.style.cursor = 'pointer';
        }

        if (tooltip) {
          const data = hitMesh.userData.nodeData;
          const galaxy = hitMesh.userData.galaxy;
          const label = data.text || data.label || 'Memory Engram';
          const cleanLabel = label.length > 55 ? label.slice(0, 52) + '...' : label;
          const access = data.access_count || 1;
          const imp = (typeof data.importance === 'number' ? data.importance : 1.0).toFixed(2);

          tooltip.innerHTML = `
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:4px;">
              <span style="font-weight:700; color:${galaxy.hex}; font-size:10px; text-transform:uppercase;">${galaxy.name}</span>
              <span style="font-size:10px; color:#9AA0A6;">Access: ${access}</span>
            </div>
            <div style="font-weight:500; font-size:12px; color:#EDEFF2; line-height:1.3; margin-bottom:4px;">${cleanLabel}</div>
            <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#F5E6AB;">
              <span>Imp: ${imp}</span>
              <span style="color:#00E5FF; font-weight:600;">Click to inspect &rarr;</span>
            </div>
          `;

          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          tooltip.style.left = `${Math.min(x, rect.width - 240)}px`;
          tooltip.style.top = `${Math.max(20, y - 10)}px`;
          tooltip.classList.add('visible');
        }

        if (typeof this.onNodeHoverCallback === 'function') {
          this.onNodeHoverCallback(hitMesh.userData.nodeData, event);
        }
      } else {
        if (this.hoveredNode && !this.hoveredNode.userData.isPulsing) {
          this.hoveredNode.material.emissiveIntensity = 0.55;
        }
        this.hoveredNode = null;
        this.renderer.domElement.style.cursor = 'grab';

        if (tooltip) {
          tooltip.classList.remove('visible');
        }

        if (typeof this.onNodeHoverCallback === 'function') {
          this.onNodeHoverCallback(null, event);
        }
      }
    }

    handleNodeClick(event) {
      if (this.hoveredNode) {
        if (this.hoveredNode.userData && this.hoveredNode.userData.isNetrunnerCore) {
          this.focusGalaxy('core');
          this.triggerSleepReplayCascade({ reinforced_synapses: 12, schemata_synthesized: 3, pruned_count: 0 });
          if (typeof this.onNodeClickCallback === 'function') {
            this.onNodeClickCallback(this.hoveredNode.userData.nodeData);
          }
          return;
        }

        // Interactive Shift+Click: Trace synaptic pathway between selectedNode and clicked node
        if (event && event.shiftKey && this.selectedNode && this.hoveredNode && this.selectedNode !== this.hoveredNode) {
          const sId = this.selectedNode.userData?.nodeData?.id;
          const tId = this.hoveredNode.userData?.nodeData?.id;
          if (sId && tId) {
            this.tracePathway(sId, tId);
            return;
          }
        }

        const nodeData = this.hoveredNode.userData.nodeData;
        this.focusNode(nodeData.id);

        if (typeof this.onNodeClickCallback === 'function') {
          this.onNodeClickCallback(nodeData);
        }
      } else {
        this.clearHighlights();
      }
    }

    connectSSE() {
      if (typeof EventSource === 'undefined') return;

      try {
        this.sseSource = new EventSource('/api/stream');
        this.sseSource.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'trigger') {
              this.triggerCascade(parsed.data.cascade);
            } else if (parsed.type === 'memory_created') {
              // Pulse Living Minds / Agents and refresh graph data
              if (window.fetchGraphData) window.fetchGraphData();
            } else if (parsed.type === 'neuromodulator_pulse') {
              // Color pulse across the nebula
              this.flashNebulaAura();
            }
          } catch (e) {
            // Ignore heartbeat pings
          }
        };

        this.sseSource.onerror = () => {
          // Reconnect automatically handled by EventSource
        };
      } catch (err) {
        console.warn('[NebulaEngine] SSE stream unavailable:', err);
      }
    }

    flashNebulaAura() {
      if (this.stardustPoints && this.stardustPoints.material) {
        this.stardustPoints.material.opacity = 1.0;
        setTimeout(() => {
          this.stardustPoints.material.opacity = 0.75;
        }, 500);
      }
    }

    updateHudStats() {
      const engramsEl = document.getElementById('hud-engrams-count');
      const synapsesEl = document.getElementById('hud-synapses-count');
      const freqEl = document.getElementById('hud-action-freq');

      if (engramsEl) engramsEl.innerText = this.stats.totalEngrams;
      if (synapsesEl) synapsesEl.innerText = this.stats.totalSynapses;
      if (freqEl) freqEl.innerText = `${this.stats.actionFrequency.toFixed(1)} Hz`;
    }

    // Multi-hop shortest synaptic pathway tracer across 3D Bezier filaments
    tracePathway(sourceId, targetId) {
      if (this.filamentCurves.length === 0) return null;

      const allNodeIds = Array.from(this.nodeMeshes.keys());
      if (allNodeIds.length === 0) return null;

      let srcId = sourceId ? String(sourceId) : null;
      if (!srcId || !this.nodeMeshes.has(srcId)) {
        srcId = this.selectedNode ? String(this.selectedNode.userData.nodeData.id) : allNodeIds[0];
      }

      // Build graph adjacency map
      const adj = new Map();
      allNodeIds.forEach(id => adj.set(id, []));
      this.filamentCurves.forEach(item => {
        const s = String(item.sourceId);
        const t = String(item.targetId);
        if (!adj.has(s)) adj.set(s, []);
        if (!adj.has(t)) adj.set(t, []);
        adj.get(s).push({ neighbor: t, filament: item, weight: item.weight || 0.2 });
        adj.get(t).push({ neighbor: s, filament: item, weight: item.weight || 0.2 });
      });

      // If targetId not specified or same as source, pick optimal cross-galaxy destination
      let tgtId = targetId ? String(targetId) : null;
      if (!tgtId || tgtId === srcId || !this.nodeMeshes.has(tgtId)) {
        const reachable = [];
        const q = [srcId];
        const visitedSet = new Set([srcId]);
        const distMap = new Map([[srcId, 0]]);

        while (q.length > 0) {
          const u = q.shift();
          const d = distMap.get(u);
          const neighbors = adj.get(u) || [];
          for (const edge of neighbors) {
            if (!visitedSet.has(edge.neighbor)) {
              visitedSet.add(edge.neighbor);
              distMap.set(edge.neighbor, d + 1);
              q.push(edge.neighbor);
              reachable.push({ id: edge.neighbor, dist: d + 1 });
            }
          }
        }

        if (reachable.length > 0) {
          const srcMesh = this.nodeMeshes.get(srcId);
          const srcGalaxy = srcMesh?.userData?.galaxy?.id || null;
          const crossGalaxy = reachable.filter(r => {
            const m = this.nodeMeshes.get(r.id);
            return m && m.userData?.galaxy && m.userData.galaxy.id !== srcGalaxy;
          });

          if (crossGalaxy.length > 0) {
            crossGalaxy.sort((a, b) => {
              if (b.dist !== a.dist) return b.dist - a.dist;
              const impA = this.nodeMeshes.get(a.id)?.userData?.nodeData?.importance || 0;
              const impB = this.nodeMeshes.get(b.id)?.userData?.nodeData?.importance || 0;
              return impB - impA;
            });
            tgtId = crossGalaxy[0].id;
          } else {
            reachable.sort((a, b) => b.dist - a.dist);
            tgtId = reachable[0].id;
          }
        }
      }

      if (!tgtId || !this.nodeMeshes.has(tgtId)) {
        console.warn('[NebulaEngine] No destination node found for pathway trace');
        return null;
      }

      // Shortest Path BFS between srcId and tgtId
      const queue = [srcId];
      const visited = new Set([srcId]);
      const prev = new Map(); // neighborId -> { parentId, filament, weight }

      while (queue.length > 0) {
        const curr = queue.shift();
        if (curr === tgtId) break;
        const neighbors = adj.get(curr) || [];
        for (const edge of neighbors) {
          if (!visited.has(edge.neighbor)) {
            visited.add(edge.neighbor);
            prev.set(edge.neighbor, { parentId: curr, filament: edge.filament, weight: edge.weight });
            queue.push(edge.neighbor);
          }
        }
      }

      if (!prev.has(tgtId) && srcId !== tgtId) {
        this.showPathwayNarration({
          notFound: true,
          srcData: this.nodeMeshes.get(srcId)?.userData?.nodeData,
          tgtData: this.nodeMeshes.get(tgtId)?.userData?.nodeData,
        });
        return null;
      }

      // Reconstruct path
      const pathNodes = [];
      const pathFilaments = [];
      let totalWeight = 0;
      let curr = tgtId;
      while (curr !== srcId) {
        pathNodes.unshift(curr);
        const info = prev.get(curr);
        if (!info) break;
        pathFilaments.unshift(info.filament);
        totalWeight += (info.weight || 0.2);
        curr = info.parentId;
      }
      pathNodes.unshift(srcId);

      const hops = pathFilaments.length;
      const avgWeight = hops > 0 ? (totalWeight / hops) : 1.0;

      // Visual Synaptic Highlighting
      this.clearHighlights();
      this.activePathway = { nodes: pathNodes, filaments: pathFilaments };

      // Dim non-path filaments
      const pathFilamentSet = new Set(pathFilaments);
      this.filamentCurves.forEach(f => {
        if (pathFilamentSet.has(f)) {
          f.line.material.opacity = 1.0;
          f.line.material.color.setHex(0xFFD700);
        } else {
          f.line.material.opacity = 0.08;
        }
      });

      // Dim non-path nodes, spotlight path nodes
      const pathNodeSet = new Set(pathNodes);
      this.nodeMeshes.forEach((mesh, id) => {
        if (pathNodeSet.has(id)) {
          mesh.material.emissiveIntensity = 1.6;
        } else {
          mesh.material.emissiveIntensity = 0.2;
        }
      });

      // Smooth Camera Glide to frame the pathway
      const pathCenter = new THREE.Vector3();
      pathNodes.forEach(id => {
        const m = this.nodeMeshes.get(id);
        if (m) pathCenter.add(m.position);
      });
      pathCenter.divideScalar(pathNodes.length);

      const srcPos = this.nodeMeshes.get(srcId).position;
      const tgtPos = this.nodeMeshes.get(tgtId).position;
      const spanDist = srcPos.distanceTo(tgtPos);
      const camDist = Math.max(160, Math.min(650, spanDist * 1.15));

      const camTarget = new THREE.Vector3(
        pathCenter.x + 30,
        pathCenter.y + 40,
        pathCenter.z + camDist
      );
      this.glideCameraTo(camTarget, pathCenter, 1.4);

      // Staggered Traveling Plasma Bursts along each hop
      const hopDelay = 340;
      for (let i = 0; i < hops; i++) {
        const filament = pathFilaments[i];
        const stepSrcId = pathNodes[i];
        const stepTgtId = pathNodes[i + 1];
        const stepSrcMesh = this.nodeMeshes.get(stepSrcId);
        const stepTgtMesh = this.nodeMeshes.get(stepTgtId);

        setTimeout(() => {
          if (stepSrcMesh) {
            this.flashNode(stepSrcMesh, i === 0 ? 0xFFD700 : 0x00E5FF, 2.0);
            this.fireShockwave(stepSrcMesh.position, i === 0 ? 0xD4AF37 : 0x00E5FF, 1.8);
          }

          if (this.audio) {
            const toneFreq = 440 * Math.pow(1.05946, (i * 2) % 12);
            this.audio.playActionPotential(toneFreq);
          }

          this.spawnPathwayBurst(filament.curve, 0xFFD700, 2.6);
          setTimeout(() => {
            this.spawnPathwayBurst(filament.curve, 0x00E5FF, 2.2);
          }, 80);

          if (i === hops - 1) {
            setTimeout(() => {
              if (stepTgtMesh) {
                this.flashNode(stepTgtMesh, 0xFFD700, 2.4);
                this.fireShockwave(stepTgtMesh.position, 0xFFD700, 2.6);
              }
              if (this.audio) {
                this.audio.playActionPotential(880);
              }
            }, 300);
          }
        }, i * hopDelay);
      }

      // Live HUD Narration Banner
      this.showPathwayNarration({
        pathNodes,
        hops,
        avgWeight,
        srcMesh: this.nodeMeshes.get(srcId),
        tgtMesh: this.nodeMeshes.get(tgtId),
      });

      return {
        path: pathNodes,
        filaments: pathFilaments,
        hops,
        avgWeight,
      };
    }

    showPathwayNarration(info) {
      let banner = document.getElementById('nebula-pathway-banner');
      if (!banner) return;

      if (info.notFound) {
        banner.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:22px;">⚡</div>
            <div style="display:flex; flex-direction:column; gap:2px;">
              <div style="font-weight:700; font-size:12px; color:#FF3366; letter-spacing:0.5px;">NO DIRECT SYNAPTIC PATHWAY FOUND</div>
              <div style="font-size:11px; color:#EDEFF2;">Engrams belong to disjoint synaptic clusters. Bridging via Netrunner Cyber-Cortex.</div>
            </div>
          </div>
        `;
        banner.classList.add('visible');
        setTimeout(() => banner.classList.remove('visible'), 4000);
        return;
      }

      const hops = info.hops;
      const latency = hops * 14;
      const avgWeight = (info.avgWeight || 0.5).toFixed(2);

      const crumbs = info.pathNodes.map((id) => {
        const m = this.nodeMeshes.get(id);
        const name = (m?.userData?.nodeData?.text || m?.userData?.nodeData?.label || id).slice(0, 16);
        const col = m?.userData?.galaxy?.hex || '#00E5FF';
        return `<span style="color:${col}; font-weight:600;">${escapeHtml(name)}</span>`;
      }).join(' <span style="color:#D4AF37;">➔</span> ');

      banner.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:18px;">⚡</span>
            <span style="font-weight:700; font-size:12px; color:#FFD700; text-transform:uppercase; letter-spacing:0.6px;">SYNAPTIC PATHWAY TRACED &bull; ${hops} HOPS</span>
          </div>
          <button style="background:transparent; border:none; color:#9AA0A6; cursor:pointer; font-size:14px; padding:0 4px;" onclick="document.getElementById('nebula-pathway-banner').classList.remove('visible')">&times;</button>
        </div>
        <div style="font-size:11px; color:#EDEFF2; line-height:1.4; max-height:48px; overflow-y:auto; font-family:var(--font-mono);">${crumbs}</div>
        <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#9AA0A6; border-top:1px solid rgba(255,255,255,0.08); padding-top:4px;">
          <span>Latency: <strong style="color:#00E5FF;">${latency} ms</strong></span>
          <span>STDP Weight: <strong style="color:#FFD700;">${avgWeight}</strong></span>
          <span>Plasticity: <strong style="color:#10B981;">3-Factor Active</strong></span>
        </div>
      `;
      banner.classList.add('visible');
      if (this.pathwayBannerTimer) clearTimeout(this.pathwayBannerTimer);
      this.pathwayBannerTimer = setTimeout(() => {
        banner.classList.remove('visible');
      }, 7000);
    }

    // Hippocampal CA3/CA1 Auto-Associative Pattern Completion Simulation
    completePattern(cueNodeId) {
      const allIds = Array.from(this.nodeMeshes.keys());
      if (allIds.length === 0) return null;

      let seedId = cueNodeId ? String(cueNodeId) : null;
      if (!seedId || !this.nodeMeshes.has(seedId)) {
        seedId = this.selectedNode ? String(this.selectedNode.userData.nodeData.id) : allIds[0];
      }

      const seedMesh = this.nodeMeshes.get(seedId);
      if (!seedMesh) return null;

      // 1. CA3 Auto-Associative Recurrent Collaterals Reverberation
      this.flashNode(seedMesh, 0x00E5FF, 2.4);
      this.fireShockwave(seedMesh.position, 0x00E5FF, 2.2);
      if (this.audio) this.audio.playActionPotential(480);

      const recurrentFilaments = this.filamentCurves.filter(
        f => f.sourceId === seedId || f.targetId === seedId
      );
      const completedNodeIds = [seedId];

      recurrentFilaments.forEach((f, idx) => {
        const neighborId = f.sourceId === seedId ? f.targetId : f.sourceId;
        completedNodeIds.push(neighborId);
        const neighborMesh = this.nodeMeshes.get(neighborId);

        setTimeout(() => {
          if (neighborMesh) {
            this.flashNode(neighborMesh, 0xFFD700, 1.8);
            this.fireShockwave(neighborMesh.position, 0xD4AF37, 1.6);
          }
          this.spawnPathwayBurst(f.curve, 0xFFD700, 2.2);
          if (this.audio) this.audio.playActionPotential(540 + idx * 30);
        }, 120 + idx * 90);
      });

      // 2. Schaffer Collateral Projection into CA1 & Netrunner Cyber-Cortex Core
      const schafferDelay = 150 + recurrentFilaments.length * 90;
      setTimeout(() => {
        if (this.netrunnerCore && this.netrunnerCore.innerCoreMesh) {
          this.fireShockwave(new THREE.Vector3(0, 0, 0), 0x00E5FF, 3.0);
          this.fireShockwave(new THREE.Vector3(0, 0, 0), 0xD4AF37, 2.2);
          if (this.audio) this.audio.playSleepRipple();
        }
      }, schafferDelay);

      // 3. HUD notification
      let banner = document.getElementById('nebula-pathway-banner');
      if (banner) {
        banner.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:18px;">🧠</span>
              <span style="font-weight:700; font-size:12px; color:#00E5FF; text-transform:uppercase; letter-spacing:0.6px;">
                CA3/CA1 PATTERN COMPLETION ENGAGED
              </span>
            </div>
            <button style="background:transparent; border:none; color:#9AA0A6; cursor:pointer; font-size:14px;" onclick="document.getElementById('nebula-pathway-banner').classList.remove('visible')">&times;</button>
          </div>
          <div style="font-size:11px; color:#EDEFF2; line-height:1.4;">
            Recurrent CA3 collaterals auto-associated ${completedNodeIds.length} memory features from cue engram. Projected via Schaffer collaterals to Netrunner Cortex.
          </div>
          <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#9AA0A6; padding-top:4px; border-top:1px solid rgba(255,255,255,0.08);">
            <span>Recurrent Density: <strong style="color:#FFD700;">${recurrentFilaments.length} Synapses</strong></span>
            <span>Schaffer Relay: <strong style="color:#10B981;">Nominal (CA1)</strong></span>
          </div>
        `;
        banner.classList.add('visible');
        if (this.pathwayBannerTimer) clearTimeout(this.pathwayBannerTimer);
        this.pathwayBannerTimer = setTimeout(() => {
          banner.classList.remove('visible');
        }, 6500);
      }

      return completedNodeIds;
    }

    // 3D Camera Orbit Tour Mode across all 6 Galaxies + Netrunner Cyber-Cortex
    toggleTourMode() {
      if (this.isTouring) {
        this.stopTour();
      } else {
        this.startTour();
      }
    }

    startTour() {
      this.isTouring = true;
      this.tourStep = 0;
      this.updateTourButtonUI(true);
      this.runTourStep();
    }

    stopTour() {
      this.isTouring = false;
      if (this.tourTimer) {
        clearTimeout(this.tourTimer);
        this.tourTimer = null;
      }
      this.hideTourNarration();
      this.updateTourButtonUI(false);
      const autoRotateEl = document.getElementById('auto-rotate-check');
      if (this.controls && autoRotateEl) {
        this.controls.autoRotate = autoRotateEl.checked;
      }
    }

    runTourStep() {
      if (!this.isTouring) return;

      if (this.tourStep >= this.tourStops.length) {
        this.showTourCompletionBanner();
        this.stopTour();
        return;
      }

      const stop = this.tourStops[this.tourStep];

      // Highlight navigator button in HUD
      document.querySelectorAll('.galaxy-nav-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById(`gnav-${stop.id}`) || document.getElementById('gnav-all');
      if (activeBtn) activeBtn.classList.add('active');

      // Clear highlights and glide camera smoothly to this stop
      this.clearHighlights();
      this.glideCameraTo(stop.camPos, stop.lookAt, 1.6);

      // Audio & shockwaves
      if (this.audio) {
        const tone = 440 + this.tourStep * 55;
        this.audio.playActionPotential(tone);
      }
      this.fireShockwave(stop.lookAt, stop.color, 2.4);

      // Flash local nodes in this cluster
      if (stop.id !== 'all') {
        const clusterMeshes = Array.from(this.nodeMeshes.values()).filter(m => {
          if (stop.id === 'core') return m.userData && m.userData.isNetrunnerCore;
          return m.userData && m.userData.galaxy && m.userData.galaxy.id === stop.id;
        });
        clusterMeshes.slice(0, 10).forEach((mesh, idx) => {
          setTimeout(() => {
            this.flashNode(mesh, stop.color, 1.8);
          }, 300 + idx * 80);
        });
      }

      // Display Live HUD Narration Card
      this.showTourNarration(stop, this.tourStep, this.tourStops.length);

      // Schedule next stop after dwell time (5200ms)
      this.tourStep++;
      this.tourTimer = setTimeout(() => {
        this.runTourStep();
      }, 5200);
    }

    showTourNarration(stop, stepIndex, totalSteps) {
      let banner = document.getElementById('nebula-tour-banner');
      if (!banner) return;

      let clusterEngrams = 0;
      if (stop.id === 'all') {
        clusterEngrams = this.stats.totalEngrams;
      } else if (stop.id === 'core') {
        clusterEngrams = 1;
      } else {
        clusterEngrams = Array.from(this.nodeMeshes.values()).filter(
          m => m.userData && m.userData.galaxy && m.userData.galaxy.id === stop.id
        ).length;
      }

      banner.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:6px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:18px;">${stop.icon}</span>
            <span style="font-weight:700; font-size:12px; color:${stop.hex}; text-transform:uppercase; letter-spacing:0.8px;">
              ✦ TOUR [${stepIndex + 1}/${totalSteps}]: ${stop.name}
            </span>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:10px; color:#9AA0A6; font-family:var(--font-mono);">Engrams: <strong style="color:#EDEFF2;">${clusterEngrams}</strong></span>
            <button style="background:transparent; border:none; color:#9AA0A6; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onclick="window.nebulaApp && window.nebulaApp.stopTour()">&times;</button>
          </div>
        </div>
        <div style="font-size:12px; color:#EDEFF2; line-height:1.4; font-weight:400;">
          ${stop.narration}
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#9AA0A6; font-family:var(--font-mono); padding-top:4px;">
          <span style="color:#00E5FF;">${stop.telemetry}</span>
          <span style="color:#D4AF37;">Next Stop in 5s &rarr;</span>
        </div>
        <div class="tour-progress-bar-wrap">
          <div class="tour-progress-bar-fill" style="background:${stop.hex};"></div>
        </div>
      `;
      banner.classList.add('visible');
    }

    hideTourNarration() {
      const banner = document.getElementById('nebula-tour-banner');
      if (banner) banner.classList.remove('visible');
    }

    showTourCompletionBanner() {
      const banner = document.getElementById('nebula-tour-banner');
      if (!banner) return;
      banner.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:22px;">✦</span>
          <div>
            <div style="font-weight:700; font-size:12px; color:#FFD700; letter-spacing:0.6px;">3D NEURAL GALAXY TOUR COMPLETE</div>
            <div style="font-size:11px; color:#EDEFF2;">Panoramic Cosmic Substrate engaged. All 6 galaxies and Netrunner Core synchronized.</div>
          </div>
        </div>
      `;
      banner.classList.add('visible');
      setTimeout(() => {
        banner.classList.remove('visible');
      }, 4500);
    }

    updateTourButtonUI(isActive) {
      const btn = document.getElementById('btn-galaxy-tour');
      if (!btn) return;
      if (isActive) {
        btn.innerHTML = '⏹ Stop Galaxy Tour';
        btn.style.borderColor = '#FF3366';
        btn.style.color = '#FF809B';
        btn.style.background = 'rgba(255, 51, 102, 0.18)';
        btn.title = 'Stop Cinematic 3D Tour';
      } else {
        btn.innerHTML = '✦ 3D Galaxy Tour';
        btn.style.borderColor = '#00E5FF';
        btn.style.color = '#00E5FF';
        btn.style.background = 'transparent';
        btn.title = 'Start Cinematic 3D Tour across all 6 Galaxies & Netrunner Core';
      }
    }

    // ==============================================================================
    // ✦ WAVE 3: INTERACTIVE 3D NEUROMODULATOR AURA SWITCHER
    // ==============================================================================
    setNeuromodulatorMode(mode) {
      const modeKey = String(mode || '').toLowerCase().trim();
      const state = NEUROMODULATOR_MODES[modeKey] || NEUROMODULATOR_MODES.balanced;
      this.currentNeuromodulator = state.id;
      this.neuromodulatorState = state;
      this.stats.actionFrequency = state.pulseFrequency;

      // 1. Transform Netrunner Cyber-Cortex 3D Core Model
      if (this.netrunnerCore) {
        const nc = this.netrunnerCore;
        if (nc.innerCoreMesh && nc.innerCoreMesh.material) {
          nc.innerCoreMesh.material.color.setHex(state.colorNum);
          nc.innerCoreMesh.material.emissive.setHex(state.colorNum);
          nc.innerCoreMesh.material.emissiveIntensity = state.coreEmissiveIntensity;
          const s = state.coreScaleMultiplier;
          nc.innerCoreMesh.scale.set(s, s, s);
        }
        if (nc.brainWireMesh && nc.brainWireMesh.material) {
          nc.brainWireMesh.material.color.setHex(state.secondaryNum);
          nc.brainWireMesh.material.opacity = Math.min(0.9, state.filamentOpacity + 0.1);
        }
        if (nc.visorMesh && nc.visorMesh.material) {
          nc.visorMesh.material.color.setHex(state.colorNum);
        }
        if (nc.gimbal1 && nc.gimbal1.material) {
          nc.gimbal1.material.color.setHex(state.colorNum);
          nc.gimbal1.material.opacity = Math.min(0.95, state.filamentOpacity + 0.2);
        }
        if (nc.gimbal2 && nc.gimbal2.material) {
          nc.gimbal2.material.color.setHex(state.secondaryNum);
          nc.gimbal2.material.opacity = Math.min(0.85, state.filamentOpacity + 0.1);
        }
        if (nc.gimbal3 && nc.gimbal3.material) {
          nc.gimbal3.material.color.setHex(state.colorNum);
          nc.gimbal3.material.opacity = Math.min(0.75, state.filamentOpacity);
        }
        if (nc.spineGroup && nc.spineGroup.children) {
          nc.spineGroup.children.forEach((disc, i) => {
            if (disc.material) {
              const col = i % 2 === 0 ? state.colorNum : state.secondaryNum;
              disc.material.color.setHex(col);
              disc.material.emissive.setHex(col);
              disc.material.emissiveIntensity = state.coreEmissiveIntensity * 0.7;
            }
          });
        }
      }

      // 2. Modulate Synaptic Filaments
      this.filamentCurves.forEach(item => {
        if (!item.line || !item.line.material) return;
        const weight = item.weight || 0.2;
        if (state.id === 'acetylcholine') {
          item.line.material.color.setHex(weight >= 0.5 ? 0x06B6D4 : 0x00E5FF);
          item.line.material.opacity = Math.max(0.65, weight * 0.95);
        } else if (state.id === 'dopamine') {
          item.line.material.color.setHex(0xF59E0B);
          item.line.material.opacity = Math.max(0.5, weight * 0.85);
        } else if (state.id === 'norepinephrine') {
          item.line.material.color.setHex(0xF43F5E);
          item.line.material.opacity = Math.max(0.55, weight * 0.9);
        } else if (state.id === 'serotonin') {
          item.line.material.color.setHex(0xA855F7);
          item.line.material.opacity = Math.max(0.3, weight * 0.55);
        } else {
          if (weight >= 0.6) {
            item.line.material.color.setHex(0xFFD700);
            item.line.material.opacity = 0.9;
          } else if (weight >= 0.3) {
            item.line.material.color.setHex(0x00E5FF);
            item.line.material.opacity = 0.65;
          } else {
            item.line.material.color.setHex(0x4A6CF7);
            item.line.material.opacity = 0.35;
          }
        }
      });

      // 3. Shockwave Aura Explosion from Netrunner Cyber-Cortex
      this.fireShockwave(new THREE.Vector3(0, 0, 0), state.colorNum, 2.6);
      if (state.id === 'norepinephrine') {
        setTimeout(() => {
          this.fireShockwave(new THREE.Vector3(0, 0, 0), state.secondaryNum, 3.2);
        }, 120);
      }

      // 4. Bio-Resonant Audio Synthesis
      if (this.audio) {
        if (state.id === 'dopamine') this.audio.playActionPotential(660);
        else if (state.id === 'norepinephrine') this.audio.playActionPotential(880);
        else if (state.id === 'acetylcholine') this.audio.playActionPotential(440);
        else if (state.id === 'serotonin') this.audio.playSleepRipple();
        else this.audio.playActionPotential(528);
      }

      // 5. Update DOM HUD telemetry
      const hudNeuromod = document.getElementById('hud-neuromod-state');
      if (hudNeuromod) {
        hudNeuromod.textContent = state.label;
        hudNeuromod.style.color = state.colorHex;
      }
      const hudFreq = document.getElementById('hud-action-freq');
      if (hudFreq) {
        hudFreq.textContent = state.pulseFrequency.toFixed(1) + ' Hz';
        hudFreq.style.color = state.colorHex;
      }

      // 6. Update Neuromodulator Buttons in HUD
      document.querySelectorAll('.neuromod-pill').forEach(btn => {
        btn.classList.toggle('active', btn.id === 'neuromod-' + state.id);
      });

      this.updateHudStats();
      return state;
    }

    // ==============================================================================
    // ✦ WAVE 3: REAL-TIME 3D ENGRAM BIRTH PROJECTILE & SLINGSHOT
    // ==============================================================================
    spawnTrailingSparkle(pos, colorNum = 0xFFD700) {
      const sparkGeo = new THREE.SphereGeometry(0.9, 8, 8);
      const sparkMat = new THREE.MeshBasicMaterial({
        color: colorNum,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const spark = new THREE.Mesh(sparkGeo, sparkMat);
      spark.position.copy(pos);
      spark.position.x += (Math.random() - 0.5) * 4;
      spark.position.y += (Math.random() - 0.5) * 4;
      spark.position.z += (Math.random() - 0.5) * 4;
      this.scene.add(spark);
      this.trailingSparkles.push({
        mesh: spark,
        geo: sparkGeo,
        mat: sparkMat,
        life: 1.0,
        decay: 2.4,
      });
    }

    showEngramBirthBanner(engram, galaxy) {
      const banner = document.getElementById('nebula-birth-banner');
      if (!banner) return;
      const title = escapeHtml(engram.label || engram.text || 'Engram').slice(0, 48);
      banner.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:20px; color:${galaxy.hex};">✦</span>
          <div>
            <div style="font-weight:750; font-size:12px; color:#FFD700; letter-spacing:0.6px; text-transform:uppercase;">
              3D ENGRAM BIRTH &bull; CORTICAL FORGE
            </div>
            <div style="font-size:11px; color:#EDEFF2;">
              ${title} &rarr; <strong style="color:${galaxy.hex};">${galaxy.name}</strong>
            </div>
          </div>
        </div>
      `;
      banner.classList.add('visible');
      if (this.birthBannerTimer) clearTimeout(this.birthBannerTimer);
      this.birthBannerTimer = setTimeout(() => {
        banner.classList.remove('visible');
      }, 3400);
    }

    anchorNewEngramNode(engram, galaxy, targetPos) {
      const sphereGeo = new THREE.SphereGeometry(1, 24, 24);
      const importance = typeof engram.importance === 'number' ? engram.importance : 1.2;
      const accessCount = engram.access_count || 1;
      const nodeRadius = Math.max(3.2, Math.min(10.0, (3.2 * importance) + Math.log1p(accessCount) * 0.8));

      const mat = new THREE.MeshStandardMaterial({
        color: galaxy.color,
        emissive: galaxy.color,
        emissiveIntensity: 0.75,
        roughness: 0.25,
        metalness: 0.8,
      });

      const mesh = new THREE.Mesh(sphereGeo, mat);
      mesh.scale.set(nodeRadius, nodeRadius, nodeRadius);
      mesh.position.copy(targetPos);
      mesh.userData = {
        nodeData: engram,
        galaxy: galaxy,
        baseColor: galaxy.color,
        baseRadius: nodeRadius,
        isPulsing: false,
      };

      this.scene.add(mesh);
      this.nodeMeshes.set(String(engram.id), mesh);
      this.stats.totalEngrams = this.nodeMeshes.size;
      this.updateHudStats();
      return mesh;
    }

    createFilamentBetweenNodes(srcObj, tgtObj, weight = 0.8, color = 0xFFD700) {
      const p1 = srcObj.position;
      const p2 = tgtObj.position;
      const midPoint = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
      const dist = p1.distanceTo(p2);
      const arcHeight = Math.min(65, dist * 0.25);
      midPoint.y += arcHeight;

      const curve = new THREE.QuadraticBezierCurve3(p1, midPoint, p2);
      const points = curve.getPoints(24);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      this.scene.add(line);

      const fil = {
        curve,
        line,
        sourceId: String(srcObj.id),
        targetId: String(tgtObj.id),
        weight,
      };
      this.filamentCurves.push(fil);

      this.spawnPlasmaPulse(curve, weight, color, 2.5);
      this.stats.totalSynapses = this.filamentCurves.length;
      this.updateHudStats();
      return fil;
    }

    spawnMemoryBurst(memoryData = {}, options = {}) {
      const engram = {
        id: memoryData.id || ('engram_' + Date.now() + '_' + Math.floor(Math.random() * 1000)),
        label: memoryData.label || memoryData.text || ('ENGRAM #' + Math.floor(1000 + Math.random() * 9000)),
        text: memoryData.text || memoryData.label || 'Sovereign STDP memory engram synthesized in 3D Netrunner Cyber-Cortex.',
        category: memoryData.category || 'insight',
        agent_id: memoryData.agent_id || 'azoth',
        importance: typeof memoryData.importance === 'number' ? memoryData.importance : 1.2,
        access_count: memoryData.access_count || 1,
        tags: Array.isArray(memoryData.tags) ? memoryData.tags : ['neural', 'stdp', 'cortex'],
        created_at: memoryData.created_at || (Date.now() / 1000),
      };

      const targetGalaxy = this.determineGalaxy(engram);

      const spread = 45;
      const targetPos = new THREE.Vector3(
        targetGalaxy.center.x + (Math.random() - 0.5) * spread * 2,
        targetGalaxy.center.y + (Math.random() - 0.5) * spread * 1.5,
        targetGalaxy.center.z + (Math.random() - 0.5) * spread * 2
      );

      const inboundStart = new THREE.Vector3(
        this.camera ? this.camera.position.x * 0.5 : 0,
        (this.camera ? this.camera.position.y : 150) + 75,
        (this.camera ? this.camera.position.z * 0.5 : 200) + 50
      );
      const corePos = new THREE.Vector3(0, 0, 0);

      // High-luminance inbound projectile
      const projectileGeo = new THREE.SphereGeometry(3.5, 16, 16);
      const projectileMat = new THREE.MeshBasicMaterial({
        color: 0xFFFFFF,
        transparent: true,
        opacity: 0.98,
        blending: THREE.AdditiveBlending,
      });
      const projectile = new THREE.Mesh(projectileGeo, projectileMat);
      projectile.position.copy(inboundStart);
      this.scene.add(projectile);

      const glowTex = createGlowTexture(targetGalaxy.hex, 48);
      const glowMat = new THREE.SpriteMaterial({
        map: glowTex,
        color: targetGalaxy.color,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const glowSprite = new THREE.Sprite(glowMat);
      glowSprite.scale.set(26, 26, 1);
      projectile.add(glowSprite);

      if (this.audio) this.audio.playActionPotential(720);

      this.showEngramBirthBanner(engram, targetGalaxy);

      // PHASE 1: Inbound flight to Netrunner Cyber-Cortex core
      const inboundDuration = 520; // ms
      const inboundStartT = performance.now();

      const inboundInterval = setInterval(() => {
        const elapsed = performance.now() - inboundStartT;
        const p = Math.min(1.0, elapsed / inboundDuration);
        const ease = p * p;

        projectile.position.lerpVectors(inboundStart, corePos, ease);
        const pScale = 1.0 + Math.sin(p * Math.PI) * 0.7;
        projectile.scale.set(pScale, pScale, pScale);

        if (p >= 1.0) {
          clearInterval(inboundInterval);
          this.scene.remove(projectile);
          projectileGeo.dispose();
          projectileMat.dispose();

          // PHASE 2: Cortical Collision & Flash
          if (this.netrunnerCore && this.netrunnerCore.innerCoreMesh) {
            this.flashNode(this.netrunnerCore.innerCoreMesh, 0xFFFFFF, 2.4);
          }
          this.fireShockwave(corePos, targetGalaxy.color, 3.8);
          this.fireShockwave(corePos, 0xFFFFFF, 2.2);
          if (this.audio) this.audio.playHarmonicChord(528);

          // PHASE 3: Outbound Slingshot into Target Galaxy
          const arcMid = new THREE.Vector3(
            (corePos.x + targetPos.x) * 0.5,
            Math.max(corePos.y, targetPos.y) + 70,
            (corePos.z + targetPos.z) * 0.5
          );
          const slingshotCurve = new THREE.QuadraticBezierCurve3(corePos, arcMid, targetPos);

          const outboundGeo = new THREE.SphereGeometry(3.0, 16, 16);
          const outboundMat = new THREE.MeshBasicMaterial({
            color: targetGalaxy.color,
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending,
          });
          const outboundStar = new THREE.Mesh(outboundGeo, outboundMat);
          const outGlow = new THREE.Sprite(new THREE.SpriteMaterial({
            map: glowTex,
            color: 0xFFFFFF,
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending,
          }));
          outGlow.scale.set(22, 22, 1);
          outboundStar.add(outGlow);
          this.scene.add(outboundStar);

          const outboundDuration = 820; // ms
          const outboundStartT = performance.now();

          const outboundInterval = setInterval(() => {
            const outElapsed = performance.now() - outboundStartT;
            const outP = Math.min(1.0, outElapsed / outboundDuration);
            const outEase = 0.5 - Math.cos(outP * Math.PI) / 2;

            const curPt = slingshotCurve.getPoint(outEase);
            outboundStar.position.copy(curPt);

            if (Math.random() < 0.4) {
              this.spawnTrailingSparkle(curPt, targetGalaxy.color);
            }

            if (outP >= 1.0) {
              clearInterval(outboundInterval);
              // PHASE 4: Arrival & Star Anchoring in Target Galaxy
              this.scene.remove(outboundStar);
              outboundGeo.dispose();
              outboundMat.dispose();

              this.fireShockwave(targetPos, targetGalaxy.color, 2.5);
              if (this.audio) this.audio.playActionPotential(660);

              const newNodeMesh = this.anchorNewEngramNode(engram, targetGalaxy, targetPos);

              this.createFilamentBetweenNodes(
                { position: corePos, id: 'netrunner-core-0' },
                { position: targetPos, id: String(engram.id) },
                0.95,
                targetGalaxy.color
              );

              if (options.focusCamera !== false) {
                const camTarget = new THREE.Vector3(
                  targetPos.x + 38,
                  targetPos.y + 22,
                  targetPos.z + 70
                );
                this.glideCameraTo(camTarget, targetPos, 1.4);
              }

              setTimeout(() => {
                if (this.nodeMeshes.has(String(engram.id))) {
                  this.focusNode(engram.id);
                }
              }, 300);
            }
          }, 16);
        }
      }, 16);
      return engram;
    }

    // ==============================================================================
    // ✦ WAVE 5: 3D HIPPOCAMPAL DREAM REPLAY WAVE & CROSS-GALAXY SWR CONSOLIDATION
    // ==============================================================================
    async triggerDreamWave() {
      if (this.isDreaming) return { success: false, reason: 'Already in dream replay' };
      this.isDreaming = true;

      // 1. Panoramic Overview Camera Glide
      this.glideCameraTo(new THREE.Vector3(0, 230, 560), new THREE.Vector3(0, 0, 0), 1.8);

      // 2. Bio-Acoustic synthesis for Hippocampal SWR Theta/Gamma entrainment
      if (this.audio) {
        this.audio.playSleepRipple();
        setTimeout(() => {
          if (this.audio) this.audio.playHarmonicChord(432);
        }, 350);
      }

      // 3. Dispatch non-blocking backend consolidation
      let backendReport = null;
      try {
        fetch('/api/consolidate', { method: 'POST' })
          .then(r => r.ok ? r.json() : null)
          .then(data => { backendReport = data; })
          .catch(() => {});
      } catch (e) {}

      // 4. Construct 3D Geodesic Ripple Sphere & Dual Harmonic Rings at Core (0, 0, 0)
      const rippleGroup = new THREE.Group();
      rippleGroup.position.set(0, 0, 0);

      // 4a. Translucent Violet Geodesic Icosahedron Sphere
      const geoIco = new THREE.IcosahedronGeometry(14, 2);
      const matIco = new THREE.MeshBasicMaterial({
        color: 0xA855F7, // Deep Violet
        wireframe: true,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const meshIco = new THREE.Mesh(geoIco, matIco);
      rippleGroup.add(meshIco);

      // 4b. Inner Translucent Cyan Plasma Sphere
      const geoSphere = new THREE.SphereGeometry(12, 24, 24);
      const matSphere = new THREE.MeshBasicMaterial({
        color: 0x00E5FF, // Electric Cyan
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const meshSphere = new THREE.Mesh(geoSphere, matSphere);
      rippleGroup.add(meshSphere);

      // 4c. Dual Harmonic Expanding Ripple Rings
      const geoRing1 = new THREE.RingGeometry(12, 16, 48);
      const matRing1 = new THREE.MeshBasicMaterial({
        color: 0xA855F7,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const ring1 = new THREE.Mesh(geoRing1, matRing1);
      ring1.rotation.x = Math.PI / 3;
      rippleGroup.add(ring1);

      const geoRing2 = new THREE.RingGeometry(16, 20, 48);
      const matRing2 = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const ring2 = new THREE.Mesh(geoRing2, matRing2);
      ring2.rotation.z = Math.PI / 4;
      ring2.rotation.y = Math.PI / 6;
      rippleGroup.add(ring2);

      this.scene.add(rippleGroup);
      this.dreamWaveGroup = rippleGroup;

      // 5. Expand Geodesic Ripple Sphere outward across all 6 Galaxies
      const waveDuration = 3400; // ms
      const waveStartT = performance.now();
      const maxWaveScale = 32.0; // 14 * 32 = ~448 units radius, encompassing all galaxies

      const waveInterval = setInterval(() => {
        const elapsed = performance.now() - waveStartT;
        const progress = Math.min(1.0, elapsed / waveDuration);
        const ease = 0.5 - Math.cos(progress * Math.PI) / 2;

        const curScale = 1.0 + ease * (maxWaveScale - 1.0);
        rippleGroup.scale.set(curScale, curScale, curScale);

        meshIco.rotation.y += 0.015;
        meshIco.rotation.x += 0.008;
        ring1.rotation.z += 0.02;
        ring2.rotation.z -= 0.025;

        const fade = Math.max(0.0, 1.0 - progress);
        matIco.opacity = 0.85 * fade;
        matSphere.opacity = 0.35 * fade;
        matRing1.opacity = 0.9 * fade;
        matRing2.opacity = 0.85 * fade;

        if (progress >= 1.0) {
          clearInterval(waveInterval);
          this.scene.remove(rippleGroup);
          geoIco.dispose();
          matIco.dispose();
          geoSphere.dispose();
          matSphere.dispose();
          geoRing1.dispose();
          matRing1.dispose();
          geoRing2.dispose();
          matRing2.dispose();
          this.dreamWaveGroup = null;
        }
      }, 16);

      // 6. Display HUD narration banner with live counter
      const showDreamBanner = (count = 0) => {
        const banner = document.getElementById('nebula-sleep-banner');
        if (!banner) return;
        banner.innerHTML = `
          <div style="font-size:26px;">🌙</div>
          <div style="display:flex; flex-direction:column; gap:3px;">
            <div style="font-weight:800; font-size:12px; color:#A855F7; letter-spacing:0.7px; text-transform:uppercase;">
              HIPPOCAMPAL SWR REPLAY &bull; CROSS-GALAXY STDP CONSOLIDATION
            </div>
            <div style="font-size:11px; color:#EDEFF2;">
              Consolidating cross-galaxy engrams across 6 strata &bull;
              <strong style="color:#00E5FF;">LTP Pathways Strengthened:</strong>
              <span id="dream-ltp-counter" style="color:#FFD700; font-weight:800; font-size:12px; font-family:monospace; margin-left:4px;">+${count}</span>
            </div>
          </div>
        `;
        banner.classList.add('visible');
      };
      showDreamBanner(0);

      // 7. Find top high-importance stars across all 6 Galaxies
      const galaxiesList = ['agents', 'obsidian', 'tools', 'living_minds', 'security', 'system'];
      const galaxyTopStars = {};
      galaxiesList.forEach(gId => {
        const meshesInGalaxy = [];
        this.nodeMeshes.forEach(mesh => {
          if (mesh.userData && mesh.userData.galaxy && mesh.userData.galaxy.id === gId) {
            meshesInGalaxy.push(mesh);
          }
        });
        meshesInGalaxy.sort((a, b) => {
          const impA = a.userData?.nodeData?.importance ?? 1.0;
          const impB = b.userData?.nodeData?.importance ?? 1.0;
          return impB - impA;
        });
        galaxyTopStars[gId] = meshesInGalaxy.slice(0, 3);
      });

      // Cross-Galaxy associative pairing sequence
      const crossPairs = [
        { from: 'agents', to: 'obsidian', color: 0xE879F9 },
        { from: 'obsidian', to: 'tools', color: 0x00E5FF },
        { from: 'tools', to: 'living_minds', color: 0x10B981 },
        { from: 'living_minds', to: 'security', color: 0xFF3366 },
        { from: 'security', to: 'system', color: 0xA855F7 },
        { from: 'system', to: 'agents', color: 0xD4AF37 },
        { from: 'agents', to: 'living_minds', color: 0x00E5FF },
        { from: 'obsidian', to: 'security', color: 0xE879F9 },
        { from: 'tools', to: 'system', color: 0xF59E0B },
      ];

      let ltpCounter = 0;
      const activeDreamBeams = [];

      crossPairs.forEach((pair, idx) => {
        setTimeout(() => {
          const fromStars = galaxyTopStars[pair.from];
          const toStars = galaxyTopStars[pair.to];

          const p1 = (fromStars && fromStars.length > 0)
            ? fromStars[idx % fromStars.length].position.clone()
            : (GALAXY_CLUSTERS[pair.from]?.center || new THREE.Vector3(0, 0, 0)).clone();

          const p2 = (toStars && toStars.length > 0)
            ? toStars[idx % toStars.length].position.clone()
            : (GALAXY_CLUSTERS[pair.to]?.center || new THREE.Vector3(0, 0, 0)).clone();

          // Elevate arc high in space
          const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
          mid.y += 65;

          const curve = new THREE.QuadraticBezierCurve3(p1, mid, p2);
          const pts = curve.getPoints(32);
          const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
          const lineMat = new THREE.LineBasicMaterial({
            color: pair.color,
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending,
          });
          const beamLine = new THREE.Line(lineGeo, lineMat);
          this.scene.add(beamLine);

          // Fast associative traveling photon
          const photonGeo = new THREE.SphereGeometry(2.2, 12, 12);
          const photonMat = new THREE.MeshBasicMaterial({
            color: 0xFFFFFF,
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending,
          });
          const photonMesh = new THREE.Mesh(photonGeo, photonMat);
          photonMesh.position.copy(p1);
          this.scene.add(photonMesh);

          // Animate photon along curve
          const photonStartT = performance.now();
          const photonDuration = 480;
          const photonInterval = setInterval(() => {
            const pelapsed = performance.now() - photonStartT;
            const pp = Math.min(1.0, pelapsed / photonDuration);
            photonMesh.position.copy(curve.getPoint(pp));
            if (pp >= 1.0) {
              clearInterval(photonInterval);
              this.scene.remove(photonMesh);
              photonGeo.dispose();
              photonMat.dispose();
            }
          }, 16);

          // Flash destination and source nodes
          if (toStars && toStars.length > 0) {
            this.flashNode(toStars[idx % toStars.length], pair.color, 2.0);
          }
          if (fromStars && fromStars.length > 0) {
            this.flashNode(fromStars[idx % fromStars.length], 0xFFFFFF, 1.8);
          }

          if (this.audio) {
            this.audio.playActionPotential(520 + (idx % 6) * 60);
          }

          // Update LTP pathways counter
          ltpCounter += Math.floor(2 + Math.random() * 3);
          const counterEl = document.getElementById('dream-ltp-counter');
          if (counterEl) counterEl.textContent = `+${ltpCounter}`;

          // Keep beam visible for 1.8s then fade
          activeDreamBeams.push({ beamLine, lineGeo, lineMat });

          // Also boost permanent synaptic filament if one connects these galaxies
          const existingFil = this.filamentCurves.find(f =>
            (f.sourceId && f.targetId) &&
            ((f.sourceId.includes(pair.from) && f.targetId.includes(pair.to)) ||
             (f.sourceId.includes(pair.to) && f.targetId.includes(pair.from)))
          );
          if (existingFil && existingFil.line && existingFil.line.material) {
            existingFil.weight = Math.min(1.0, (existingFil.weight || 0.5) + 0.15);
            existingFil.line.material.opacity = 0.95;
            existingFil.line.material.color.setHex(pair.color);
          }
        }, 300 + idx * 240);
      });

      // Cleanup active dream replay beams after all pairs complete
      setTimeout(() => {
        activeDreamBeams.forEach(b => {
          this.scene.remove(b.beamLine);
          b.lineGeo.dispose();
          b.lineMat.dispose();
        });
        activeDreamBeams.length = 0;
        this.isDreaming = false;

        // Finalize banner
        const banner = document.getElementById('nebula-sleep-banner');
        if (banner) {
          banner.innerHTML = `
            <div style="font-size:26px;">🌙</div>
            <div style="display:flex; flex-direction:column; gap:3px;">
              <div style="font-weight:800; font-size:12px; color:#A855F7; letter-spacing:0.7px; text-transform:uppercase;">
                HIPPOCAMPAL CONSOLIDATION COMPLETE
              </div>
              <div style="font-size:11px; color:#EDEFF2;">
                ${ltpCounter} Cross-Galaxy LTP Pathways Strengthened &bull; Multi-Galaxy Schemata Synchronized &bull; 0 Pruned
              </div>
            </div>
          `;
          setTimeout(() => banner.classList.remove('visible'), 3400);
        }
      }, 300 + crossPairs.length * 240 + 1600);

      return {
        success: true,
        projectedLtpPathways: crossPairs.length * 2
      };
    }

    // ==============================================================================
    // ✦ WAVE 5: REAL-TIME 3D SYNAPTIC SALIENCE SCRUBBER
    // ==============================================================================
    setSalienceThreshold(minImportance = 0.0) {
      const threshold = Math.max(0.0, Math.min(0.95, parseFloat(minImportance) || 0.0));
      this.salienceThreshold = threshold;

      let illuminatedCount = 0;
      const totalCount = this.nodeMeshes.size;

      this.nodeMeshes.forEach((mesh) => {
        const data = mesh.userData?.nodeData || {};
        const rawImp = typeof data.importance === 'number' ? data.importance : 1.0;
        const normImp = rawImp > 1.0 ? Math.min(1.0, rawImp / 2.0) : rawImp;
        const baseRadius = mesh.userData?.baseRadius || 4.0;

        const meetsThreshold = normImp >= threshold;
        if (meetsThreshold) illuminatedCount++;

        if (mesh.material) {
          mesh.material.transparent = true;
          if (meetsThreshold) {
            // High-importance core engram constellation: illuminated & prominent
            mesh.material.opacity = 1.0;
            mesh.material.emissiveIntensity = 0.85 + (normImp * 0.45);
            const boostScale = threshold > 0.05 ? 1.25 : 1.0;
            mesh.scale.set(baseRadius * boostScale, baseRadius * boostScale, baseRadius * boostScale);
          } else {
            // Low-weight background star: smoothly dimmed and scaled down
            mesh.material.opacity = Math.max(0.12, 0.38 - threshold * 0.28);
            mesh.material.emissiveIntensity = 0.08;
            const dimScale = Math.max(0.35, 0.75 - threshold * 0.42);
            mesh.scale.set(baseRadius * dimScale, baseRadius * dimScale, baseRadius * dimScale);
          }
        }
      });

      // Modulate Synaptic Filaments
      this.filamentCurves.forEach((fil) => {
        if (!fil.line || !fil.line.material) return;
        const w = fil.weight || 0.5;
        fil.line.material.transparent = true;
        if (w >= threshold) {
          // Boost opacity of high-salience structural filaments
          fil.line.material.opacity = Math.min(1.0, 0.45 + threshold * 0.55);
        } else {
          // Dim non-salient background filaments
          fil.line.material.opacity = Math.max(0.04, 0.25 - threshold * 0.22);
        }
      });

      // Sync DOM controls if present
      const displayVal = document.getElementById('salience-val-display');
      if (displayVal) {
        displayVal.textContent = threshold.toFixed(2);
      }
      const slider = document.getElementById('salience-slider');
      if (slider && parseFloat(slider.value) !== threshold) {
        slider.value = threshold;
      }

      return {
        threshold,
        illuminatedCount,
        totalCount
      };
    }

    animate() {
      requestAnimationFrame(() => this.animate());

      const delta = this.clock.getDelta();
      const time = this.clock.getElapsedTime();

      // 1. Controls update
      if (this.controls && !this.isGlidingCamera) {
        this.controls.update();
      }

      // 2. Smooth camera glide
      if (this.isGlidingCamera) {
        const elapsed = time - this.glideStartTime;
        const dur = this.glideDuration || 1.4;
        const progress = Math.min(1.0, elapsed / dur);
        const ease = 0.5 - Math.cos(progress * Math.PI) / 2; // smooth cosine ease

        this.camera.position.lerpVectors(this.glideStartPos, this.glideEndPos, ease);
        if (this.controls) {
          this.controls.target.lerpVectors(this.glideStartLook, this.glideEndLook, ease);
          this.controls.update();
        }

        if (progress >= 1.0) {
          this.isGlidingCamera = false;
        }
      }

      // 3. Stardust gentle harmonic oscillation
      if (this.stardustPositions && this.stardustPoints) {
        const positions = this.stardustPoints.geometry.attributes.position.array;
        for (let i = 0; i < positions.length; i += 3) {
          positions[i + 1] += Math.sin(time * 0.8 + positions[i] * 0.015) * 0.08;
        }
        this.stardustPoints.geometry.attributes.position.needsUpdate = true;
      }

      // 4. Galaxy Cores & Netrunner Cyber-Cortex rotation
      const rotMult = this.neuromodulatorState ? this.neuromodulatorState.rotationMultiplier : 1.0;
      this.galaxyCores.forEach((c) => {
        if (c.ring) c.ring.rotation.z += 0.005 * rotMult;
      });
      if (this.netrunnerCore) {
        const nc = this.netrunnerCore;
        if (nc.brainWireMesh) {
          nc.brainWireMesh.rotation.y += 0.004 * rotMult;
          nc.brainWireMesh.rotation.x = Math.sin(time * 0.6 * rotMult) * 0.15;
        }
        if (nc.innerCoreMesh) {
          nc.innerCoreMesh.rotation.y -= 0.008 * rotMult;
          const baseScale = this.neuromodulatorState ? this.neuromodulatorState.coreScaleMultiplier : 1.0;
          const pulseScale = baseScale * (1.0 + Math.sin(time * 2.5 * rotMult) * 0.08);
          nc.innerCoreMesh.scale.set(pulseScale, pulseScale, pulseScale);
        }
        if (nc.gimbal1) {
          nc.gimbal1.rotation.z += 0.012 * rotMult;
          nc.gimbal1.rotation.x += 0.006 * rotMult;
        }
        if (nc.gimbal2) {
          nc.gimbal2.rotation.y -= 0.014 * rotMult;
          nc.gimbal2.rotation.z += 0.005 * rotMult;
        }
        if (nc.gimbal3) {
          nc.gimbal3.rotation.x += 0.01 * rotMult;
          nc.gimbal3.rotation.y += 0.008 * rotMult;
        }
      }

      // 5. Plasma Action Potential Pulses along Bezier Filaments
      const speedMult = this.neuromodulatorState ? this.neuromodulatorState.speedMultiplier : 1.0;
      for (let i = this.plasmaPulses.length - 1; i >= 0; i--) {
        const pulse = this.plasmaPulses[i];
        pulse.t += delta * pulse.speed * speedMult;
        if (pulse.t >= 1.0) {
          if (pulse.isOneShot) {
            this.scene.remove(pulse.mesh);
            if (pulse.mesh.geometry) pulse.mesh.geometry.dispose();
            if (pulse.mesh.material) pulse.mesh.material.dispose();
            this.plasmaPulses.splice(i, 1);
            continue;
          } else {
            pulse.t = 0.0;
          }
        }
        const pos = pulse.curve.getPoint(pulse.t);
        pulse.mesh.position.copy(pos);
      }

      // 5b. Update Trailing Sparkles
      for (let i = this.trailingSparkles.length - 1; i >= 0; i--) {
        const s = this.trailingSparkles[i];
        s.life -= delta * s.decay;
        if (s.life <= 0) {
          this.scene.remove(s.mesh);
          if (s.geo) s.geo.dispose();
          if (s.mat) s.mat.dispose();
          this.trailingSparkles.splice(i, 1);
        } else {
          s.mat.opacity = s.life * 0.85;
          s.mesh.scale.set(s.life, s.life, s.life);
        }
      }

      // 6. Action frequency decay toward resting baseline (1.2 Hz)
      if (this.stats.actionFrequency > 1.2) {
        this.stats.actionFrequency = Math.max(1.2, this.stats.actionFrequency - delta * 0.15);
        this.updateHudStats();
      }

      // 7. Render
      this.renderer.render(this.scene, this.camera);
    }

    /**
     * Searches 3D stars across all 6 Galaxies for query, smoothly glides camera,
     * fires arrival shockwave, traces synaptic pathway beam from (0,0,0) to star,
     * and updates #nebula-tour-banner with 🎯 3D STAR LOCKED: [GALAXY] <snippet>.
     */
    focusNodeByQuery(query) {
      const q = String(query || '').trim().toLowerCase();
      if (!q) {
        if (typeof showToast === 'function') showToast('Please enter a query or star name to locate', 'info');
        return null;
      }

      let bestMesh = null;
      let highestScore = -1;

      // Scan all node meshes across 6 galaxies in the 3D nebula
      for (const [id, mesh] of this.nodeMeshes.entries()) {
        const nodeData = mesh.userData.nodeData || {};
        const galaxy = mesh.userData.galaxy || this.determineGalaxy(nodeData);

        const text = String(nodeData.text || nodeData.label || '').toLowerCase();
        const cat = String(nodeData.category || '').toLowerCase();
        const tags = Array.isArray(nodeData.tags) ? nodeData.tags.map(t => String(t).toLowerCase()) : [];
        const gName = String(galaxy.name || '').toLowerCase();
        const gId = String(galaxy.id || '').toLowerCase();

        let score = 0;
        if (text === q || String(id) === q) score += 100;
        else if (text.startsWith(q)) score += 50;
        else if (text.includes(q)) score += 30;

        if (gId === q || gName === q) score += 40;
        else if (gName.includes(q) || gId.includes(q)) score += 20;

        if (cat === q) score += 35;
        else if (cat.includes(q)) score += 15;

        if (tags.includes(q)) score += 30;
        else if (tags.some(t => t.includes(q))) score += 15;

        if (score > highestScore) {
          highestScore = score;
          bestMesh = mesh;
        }
      }

      // If no individual engram matched, check if query matches a galaxy name directly
      if (!bestMesh || highestScore <= 0) {
        const matchedGalaxyKey = Object.keys(GALAXY_CLUSTERS).find(k => {
          const g = GALAXY_CLUSTERS[k];
          return g.id.toLowerCase().includes(q) || g.name.toLowerCase().includes(q) || q.includes(g.id.toLowerCase()) || (q.includes('obsidian') && k === 'obsidian');
        });

        if (matchedGalaxyKey) {
          const targetGalaxy = GALAXY_CLUSTERS[matchedGalaxyKey];
          const galaxyNodes = Array.from(this.nodeMeshes.values()).filter(m => {
            const g = m.userData.galaxy || this.determineGalaxy(m.userData.nodeData || {});
            return g.id === matchedGalaxyKey;
          });
          if (galaxyNodes.length > 0) {
            bestMesh = galaxyNodes[0];
          } else {
            const starData = {
              id: 'anchor-' + matchedGalaxyKey,
              label: `${targetGalaxy.name} Core Star`,
              text: `${targetGalaxy.name}: ${targetGalaxy.description}. Sovereign STDP cluster.`,
              category: matchedGalaxyKey,
              tags: [matchedGalaxyKey, 'sovereign', 'nebula', 'stdp'],
              importance: 1.5,
              access_count: 5,
            };
            bestMesh = this.anchorNewEngramNode(starData, targetGalaxy, targetGalaxy.center.clone());
          }
        }
      }

      if (!bestMesh) {
        if (typeof showToast === 'function') {
          showToast(`No 3D star found matching "${query}"`, 'warning');
        }
        return null;
      }

      const matchedNodeData = bestMesh.userData.nodeData || {};
      const galaxy = bestMesh.userData.galaxy || this.determineGalaxy(matchedNodeData);
      const starPos = bestMesh.position.clone();
      const corePos = new THREE.Vector3(0, 0, 0);

      // 1. Select and flash spotlight on matched star
      this.selectedNode = bestMesh;
      this.flashNode(bestMesh, 0x00E5FF, 2.8);

      // 2. Smoothly glide Three.js camera to focus on matched star
      const camTarget = new THREE.Vector3(
        starPos.x + 35,
        starPos.y + 20,
        starPos.z + 65
      );
      this.glideCameraTo(camTarget, starPos, 1.3);

      // 3. Fire arrival shockwave at star position
      this.fireShockwave(starPos, galaxy.color || 0x00E5FF, 2.6);
      if (this.audio) this.audio.playActionPotential(750);

      // 4. Trace a synaptic pathway beam from (0,0,0) Netrunner Core to that star
      const midControl = new THREE.Vector3(
        (corePos.x + starPos.x) * 0.5,
        (corePos.y + starPos.y) * 0.5 + 30,
        (corePos.z + starPos.z) * 0.5
      );
      const beamCurve = new THREE.QuadraticBezierCurve3(corePos, midControl, starPos);

      // Add luminous synaptic beam line to 3D scene
      const beamPoints = beamCurve.getPoints(48);
      const beamGeo = new THREE.BufferGeometry().setFromPoints(beamPoints);
      const beamMat = new THREE.LineBasicMaterial({
        color: galaxy.color || 0x00E5FF,
        transparent: true,
        opacity: 0.95,
        linewidth: 2,
      });
      const beamLine = new THREE.Line(beamGeo, beamMat);
      this.scene.add(beamLine);

      // Launch traveling plasma burst along the beam
      this.spawnPlasmaPulse(beamCurve, 1.2, 0x00E5FF, 3.5);
      setTimeout(() => {
        this.spawnPathwayBurst(beamCurve, 0xFFD700, 2.5);
      }, 120);

      // Smoothly fade out the temporary synaptic beam
      setTimeout(() => {
        let op = 0.95;
        const fadeTimer = setInterval(() => {
          op -= 0.1;
          if (op <= 0) {
            clearInterval(fadeTimer);
            this.scene.remove(beamLine);
            beamGeo.dispose();
            beamMat.dispose();
          } else {
            beamMat.opacity = op;
          }
        }, 60);
      }, 2500);

      // 5. Update #nebula-tour-banner with 🎯 3D STAR LOCKED: [GALAXY] <snippet>
      const banner = document.getElementById('nebula-tour-banner');
      if (banner) {
        const rawText = matchedNodeData.text || matchedNodeData.label || ('Engram #' + (matchedNodeData.id || ''));
        const snippet = rawText.length > 80 ? rawText.slice(0, 77) + '...' : rawText;
        const galaxyName = (galaxy.name || galaxy.id || 'COSMOS').toUpperCase();

        banner.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:18px;">🎯</span>
              <span style="font-weight:700; font-size:12px; color:${galaxy.hex || '#00E5FF'}; text-transform:uppercase; letter-spacing:0.8px;">
                3D STAR LOCKED: [${galaxyName}]
              </span>
            </div>
            <button style="background:transparent; border:none; color:#9AA0A6; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onclick="window.nebulaApp && window.nebulaApp.hideTourNarration()">&times;</button>
          </div>
          <div style="font-size:12px; color:#EDEFF2; line-height:1.4; font-weight:400; padding-top:4px;">
            ${typeof escapeHtml === 'function' ? escapeHtml(snippet) : snippet}
          </div>
          <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#9AA0A6; font-family:var(--font-mono); padding-top:4px;">
            <span style="color:#00E5FF;">Coord: [${Math.round(starPos.x)}, ${Math.round(starPos.y)}, ${Math.round(starPos.z)}]</span>
            <span style="color:#D4AF37;">Synaptic Beam: Online (0,0,0 &rarr; Star)</span>
          </div>
        `;
        banner.classList.add('visible');
      }

      if (typeof showToast === 'function') {
        showToast(`🎯 3D Star Locked: [${galaxy.name}]`, 'success');
      }

      return bestMesh;
    }

    /**
     * Serializes the live 3D Nebula topology (all 6 Galaxies, Netrunner Cyber-Cortex (0,0,0),
     * star 3D coordinates [x,y,z], active neuromodulator mode, salience threshold, and filament count).
     * Triggers a JSON download (neuro_nebula_3d_substrate.json) or returns the snapshot object,
     * and shows a HUD confirmation banner (📥 3D COSMOS SNAPSHOT EXPORTED).
     */
    export3DSubstrateSnapshot() {
      const now = new Date().toISOString();
      const stars = [];

      for (const [id, mesh] of this.nodeMeshes.entries()) {
        const nodeData = mesh.userData.nodeData || {};
        const galaxy = mesh.userData.galaxy || this.determineGalaxy(nodeData);
        stars.push({
          id: String(id),
          label: nodeData.label || nodeData.text || ('Engram ' + id),
          category: nodeData.category || 'general',
          tags: nodeData.tags || [],
          importance: typeof nodeData.importance === 'number' ? nodeData.importance : 1.0,
          access_count: nodeData.access_count || 1,
          galaxy: {
            id: galaxy.id,
            name: galaxy.name,
            hex: galaxy.hex,
          },
          coordinates: [
            parseFloat(mesh.position.x.toFixed(2)),
            parseFloat(mesh.position.y.toFixed(2)),
            parseFloat(mesh.position.z.toFixed(2)),
          ],
        });
      }

      const galaxiesSummary = Object.keys(GALAXY_CLUSTERS).map(k => {
        const g = GALAXY_CLUSTERS[k];
        const count = stars.filter(s => s.galaxy && s.galaxy.id === g.id).length;
        return {
          id: g.id,
          name: g.name,
          hex: g.hex,
          center: [g.center.x, g.center.y, g.center.z],
          starCount: count,
        };
      });

      const snapshot = {
        title: "Neuro-Memory 3D Cosmos Substrate Topology Snapshot",
        version: "3.3.0",
        timestamp: now,
        netrunnerCyberCortex: {
          hubPosition: [0, 0, 0],
          name: "Netrunner Cyber-Cortex",
          frequency: this.stats.actionFrequency || 1.2,
          plasticity: "3-Factor STDP",
        },
        neuromodulatorState: {
          current: this.currentNeuromodulator || 'balanced',
          mode: this.neuromodulatorState ? this.neuromodulatorState.name : 'Balanced',
          colorHex: this.neuromodulatorState ? this.neuromodulatorState.colorHex : '#D4AF37',
        },
        salienceThreshold: typeof this.salienceThreshold === 'number' ? this.salienceThreshold : 0.0,
        telemetry: {
          totalStars: stars.length,
          totalFilaments: this.filamentCurves.length,
          activePulses: this.plasmaPulses.length,
        },
        galaxies: galaxiesSummary,
        stars: stars,
      };

      // Trigger client-side JSON file download if supported
      try {
        if (typeof document !== 'undefined' && typeof Blob !== 'undefined' && typeof URL !== 'undefined' && URL.createObjectURL) {
          const jsonStr = JSON.stringify(snapshot, null, 2);
          const blob = new Blob([jsonStr], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'neuro_nebula_3d_substrate.json';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
      } catch (err) {
        console.warn('Snapshot download skipped:', err);
      }

      // Display HUD confirmation banner (📥 3D COSMOS SNAPSHOT EXPORTED)
      const banner = document.getElementById('nebula-tour-banner');
      if (banner) {
        banner.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:18px;">📥</span>
              <span style="font-weight:700; font-size:12px; color:#00E5FF; text-transform:uppercase; letter-spacing:0.8px;">
                3D COSMOS SNAPSHOT EXPORTED
              </span>
            </div>
            <button style="background:transparent; border:none; color:#9AA0A6; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onclick="window.nebulaApp && window.nebulaApp.hideTourNarration()">&times;</button>
          </div>
          <div style="font-size:12px; color:#EDEFF2; line-height:1.4; font-weight:400; padding-top:4px;">
            Serialized <strong>${stars.length} 3D Stars</strong> across 6 Galaxies and <strong>${this.filamentCurves.length} Synaptic Filaments</strong>.
          </div>
          <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#9AA0A6; font-family:var(--font-mono); padding-top:4px;">
            <span style="color:#D4AF37;">File: neuro_nebula_3d_substrate.json</span>
            <span style="color:#00E5FF;">Aura: ${this.currentNeuromodulator || 'balanced'}</span>
          </div>
        `;
        banner.classList.add('visible');
      }

      if (typeof showToast === 'function') {
        showToast('📥 3D Cosmos Substrate Snapshot Exported!', 'success');
      }

      return snapshot;
    }
  }

  // Expose NebulaUniverse & NebulaEngine globally
  window.NebulaUniverse = NebulaUniverse;
  window.NebulaEngine = NebulaUniverse;
})();
