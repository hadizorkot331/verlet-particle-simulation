# Verlet Particle Simulation with Space Partitioning and Image Mapping

This is a high-performance 2D particle simulation built with **Pygame** that demonstrates:
- Verlet integration for motion
- Collision resolution between thousands of particles
- Space partitioning for efficient collision detection
- Experimental multithreading support
- Image mapping based on the deterministic nature of the simulation

---
##  Features

- **Verlet Integration**: Physically realistic motion without explicit velocity.
- **Space Partitioning**: Grid-based optimization to handle collision detection at scale.
- **Multithreading (Experimental)**: Parallel collision processing by dividing columns.
- **Image-Based Coloring**: Provide an image path when running the code, then press `SPACE` after particles have settled in order to add them again with an image overlayed on top (deterministic physics).

## Insipiration

- This project was inspired by https://github.com/johnBuffer/VerletSFML-Multithread
---