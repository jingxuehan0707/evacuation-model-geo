---
title: 'PyFire-Evac: An interdisciplinary agent-based modeling package for wildfire evacuation with minimal coding'
tags:
  - Python
  - agent-based modeling
  - wildfire evacuation
  - emergency management
  - geospatial analysis
authors:
  - name: Xuehan Jing
    orcid: 0009-0002-0870-3766
    affiliation: 1
affiliations:
  - name: Clemson University, USA
    index: 1
date: 19 January 2026
bibliography: paper.bib
---

# Summary

PyFire-Evac is an interdisciplinary Agent-Based Modeling (ABM) python package designed for wildfire evacuation simulations with minimal programming requirements. Developed as an extension of the [mesa](https://mesa.readthedocs.io/latest/) and [mesa-geo](https://mesa-geo.readthedocs.io/stable/index.html) frameworks, the package facilitates the creation of simulations through the interaction of agents representing natural systems, the built environment, and social systems. The software enables the integration of fire dynamics, population distribution, road networks, and shelter locations, while allowing for the configuration of model-level parameters including traffic dynamics and household decision-making processes. By utilizing a streamlined codebase, researchers and emergency management professionals can establish wildfire evacuation models with flexible configurations. This package is intended to support emergency management research, particularly for individuals new to agent-based modeling who seek to examine the application of such models within the context of wildfire emergency response.

# Statement of need

[Describe why this software is needed, what gap it fills, and who the target audience is]

Existing open-source agent-based modeling (ABM) platforms, including NetLogo, Mesa, GAMA, and MASON, provide foundational architectures for generalized simulations; however, these frameworks require substantial development effort to implement complex evacuation models. While NetLogo offers a reduced effort for model construction, it requires proficiency in the proprietary NetLogo programming language. The Mesa ecosystem, with the Mesa-geo extension, provides a Python-based alternative, yet agent-level methods remain constrained, often requiring the development of custom methods to facilitate complex agent interactions. GAMA enables sophisticated spatial representations but demands knowledge of object-oriented programming and the native GAMA Modeling Language (GAML). MASON demonstrates high performance for large-scale simulations but entails a high modeling burden, generally limiting itself to users with advanced Java programming experience. Furthermore, while these platforms include evacuation examples, such examples are frequently simplified for educational purposes regarding the software rather than the representation of agent interactions. The PyFire-Evac package is developed to reduce the development effort for constructing wildfire evacuation models that incorporate detailed agent interactions, specifically for researchers with basic Python proficiency. Because the package is integrated into the Python ecosystem, it facilitates the incorporation of Large Language Model (LLM) frameworks to support agent-level decision-making processes, leveraging the established support for LLMs within the Python community.

# State of the field

[Discuss existing tools and how this software compares or improves upon them]

# Implementation

[Describe the key features and implementation details of the software]

# Usage

[Provide examples of how the software is used]

# Acknowledgements

[Include acknowledgements for funding, contributions, etc.]

# References
