// Three.js background for futuristic dashboard
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.module.js';

class ThreeScene {
    constructor() {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        
        this.init();
    }
    
    init() {
        // Setup renderer
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setClearColor(0x000000, 0);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        
        // Add canvas to background
        const background = document.getElementById('three-background');
        if (background) {
            background.appendChild(this.renderer.domElement);
        }
        
        // Create particles
        this.createParticles();
        
        // Position camera
        this.camera.position.z = 5;
        
        // Handle resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation
        this.animate();
    }
    
    createParticles() {
        const particlesGeometry = new THREE.BufferGeometry();
        const particlesCount = 1000;
        
        const posArray = new Float32Array(particlesCount * 3);
        
        for (let i = 0; i < particlesCount * 3; i++) {
            posArray[i] = (Math.random() - 0.5) * 10;
        }
        
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        
        const particlesMaterial = new THREE.PointsMaterial({
            size: 0.02,
            color: 0x00ffff,
            transparent: true,
            opacity: 0.8
        });
        
        this.particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
        this.scene.add(this.particlesMesh);
    }
    
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.particlesMesh) {
            this.particlesMesh.rotation.y += 0.001;
            this.particlesMesh.rotation.x += 0.0005;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize Three.js scene when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('three-background')) {
        new ThreeScene();
    }
});