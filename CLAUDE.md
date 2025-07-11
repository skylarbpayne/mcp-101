# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains materials for "MCP 101" - a Quarto presentation designed to teach engineers how to build applications using LLMs with the Model Context Protocol (MCP). The project includes both an example demonstration project and a presentation to showcase the content.

## Development Commands

### Quarto Commands
- `quarto preview` - Start development server with live reload
- `quarto render` - Build the presentation 
- `quarto render --to revealjs` - Explicitly render as reveal.js presentation
- `quarto check` - Verify Quarto installation and project configuration

### Project Structure
- Main presentation should be in `index.qmd` or similar `.qmd` file
- Configuration in `_quarto.yml` 
- Example/demo code in dedicated directories (e.g., `examples/`, `demo/`)
- Static assets (images, etc.) typically in `images/` or `assets/`

## Content Guidelines

### Presentation Style
- Use standard QML syntax without custom CSS/HTML styling
- Focus on informative, engaging slides with minimal text
- Target audience: engineers learning to build LLM applications
- Slides should demonstrate concepts rather than just explain them

### MCP Content Focus
- Practical examples of MCP implementation
- Code demonstrations that engineers can follow
- Real-world use cases and applications
- Hands-on examples that complement the presentation

## Architecture Notes

This is a Quarto-based presentation project where:
- `.qmd` files contain slide content using Quarto markdown
- `_quarto.yml` configures presentation format and options
- Example projects demonstrate MCP concepts in practice
- The presentation and examples work together to teach MCP implementation

When working on this project, prioritize creating clear, practical demonstrations over theoretical explanations.