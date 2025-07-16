#!/usr/bin/env python3
"""
GitHub Integration Module for OAuth Research Assistant

This module provides GitHub API integration with proper OAuth 2.1 authentication,
demonstrating secure API access patterns for MCP servers.
"""

import base64
import httpx
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class GitHubRepository:
    """GitHub repository information"""
    id: int
    name: str
    full_name: str
    html_url: str
    description: Optional[str]
    private: bool
    created_at: str
    updated_at: str

@dataclass
class GitHubGist:
    """GitHub gist information"""
    id: str
    html_url: str
    description: str
    public: bool
    created_at: str
    updated_at: str
    files: Dict[str, dict]

class GitHubClient:
    """GitHub API client with OAuth 2.1 support"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-OAuth-Research-Assistant/1.0"
        }
    
    async def get_user_info(self) -> Dict:
        """Get authenticated user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_repository(
        self, 
        name: str, 
        description: str = "", 
        private: bool = False,
        auto_init: bool = True
    ) -> GitHubRepository:
        """Create a new GitHub repository"""
        
        repo_data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "gitignore_template": "Python"  # Add Python gitignore
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                json=repo_data
            )
            response.raise_for_status()
            data = response.json()
            
            return GitHubRepository(
                id=data["id"],
                name=data["name"],
                full_name=data["full_name"],
                html_url=data["html_url"],
                description=data["description"],
                private=data["private"],
                created_at=data["created_at"],
                updated_at=data["updated_at"]
            )
    
    async def create_file(
        self, 
        repo_full_name: str, 
        file_path: str, 
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> Dict:
        """Create or update a file in a repository"""
        
        file_data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/repos/{repo_full_name}/contents/{file_path}",
                headers=self.headers,
                json=file_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_gist(
        self, 
        description: str, 
        files: Dict[str, str],
        public: bool = False
    ) -> GitHubGist:
        """Create a new GitHub Gist"""
        
        gist_files = {}
        for filename, content in files.items():
            gist_files[filename] = {"content": content}
        
        gist_data = {
            "description": description,
            "public": public,
            "files": gist_files
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/gists",
                headers=self.headers,
                json=gist_data
            )
            response.raise_for_status()
            data = response.json()
            
            return GitHubGist(
                id=data["id"],
                html_url=data["html_url"],
                description=data["description"],
                public=data["public"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                files=data["files"]
            )
    
    async def list_repositories(self, per_page: int = 30) -> List[GitHubRepository]:
        """List user repositories"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                params={"per_page": per_page, "sort": "updated"}
            )
            response.raise_for_status()
            data = response.json()
            
            repositories = []
            for repo_data in data:
                repositories.append(GitHubRepository(
                    id=repo_data["id"],
                    name=repo_data["name"],
                    full_name=repo_data["full_name"],
                    html_url=repo_data["html_url"],
                    description=repo_data["description"],
                    private=repo_data["private"],
                    created_at=repo_data["created_at"],
                    updated_at=repo_data["updated_at"]
                ))
            
            return repositories
    
    async def list_gists(self, per_page: int = 30) -> List[GitHubGist]:
        """List user gists"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/gists",
                headers=self.headers,
                params={"per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()
            
            gists = []
            for gist_data in data:
                gists.append(GitHubGist(
                    id=gist_data["id"],
                    html_url=gist_data["html_url"],
                    description=gist_data["description"],
                    public=gist_data["public"],
                    created_at=gist_data["created_at"],
                    updated_at=gist_data["updated_at"],
                    files=gist_data["files"]
                ))
            
            return gists

class ResearchPaperRepository:
    """Specialized class for managing research paper repositories on GitHub"""
    
    def __init__(self, github_client: GitHubClient):
        self.github = github_client
    
    async def create_paper_repository(
        self, 
        paper_title: str,
        paper_id: str,
        authors: List[str],
        abstract: str,
        pdf_url: str,
        arxiv_url: str,
        categories: List[str],
        published_date: str
    ) -> GitHubRepository:
        """Create a repository specifically for a research paper"""
        
        # Sanitize repository name
        repo_name = self._sanitize_repo_name(f"{paper_id}-{paper_title}")
        
        # Create repository
        repo = await self.github.create_repository(
            name=repo_name,
            description=f"Research paper: {paper_title}",
            private=False,
            auto_init=True
        )
        
        # Create comprehensive README
        readme_content = self._generate_paper_readme(
            paper_title, paper_id, authors, abstract, 
            pdf_url, arxiv_url, categories, published_date
        )
        
        await self.github.create_file(
            repo_full_name=repo.full_name,
            file_path="README.md",
            content=readme_content,
            commit_message="Add comprehensive paper information"
        )
        
        # Create paper metadata file
        metadata_content = self._generate_metadata_file(
            paper_title, paper_id, authors, abstract,
            pdf_url, arxiv_url, categories, published_date
        )
        
        await self.github.create_file(
            repo_full_name=repo.full_name,
            file_path="paper_metadata.json",
            content=metadata_content,
            commit_message="Add machine-readable paper metadata"
        )
        
        # Create notes template
        notes_content = self._generate_notes_template(paper_title)
        
        await self.github.create_file(
            repo_full_name=repo.full_name,
            file_path="research_notes.md",
            content=notes_content,
            commit_message="Add research notes template"
        )
        
        return repo
    
    def _sanitize_repo_name(self, name: str) -> str:
        """Sanitize a string to be a valid GitHub repository name"""
        # Remove special characters and replace spaces with hyphens
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '-', name)
        sanitized = re.sub(r'-+', '-', sanitized)  # Remove multiple consecutive hyphens
        sanitized = sanitized.strip('-.')  # Remove leading/trailing hyphens and dots
        
        # Ensure it's not too long
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized or "research-paper"
    
    def _generate_paper_readme(
        self, title: str, paper_id: str, authors: List[str], 
        abstract: str, pdf_url: str, arxiv_url: str, 
        categories: List[str], published_date: str
    ) -> str:
        """Generate a comprehensive README for the paper repository"""
        return f"""# {title}

[![ArXiv](https://img.shields.io/badge/arXiv-{paper_id}-b31b1b.svg)](https://arxiv.org/abs/{paper_id})
[![PDF](https://img.shields.io/badge/PDF-Download-red.svg)]({pdf_url})

## 📄 Paper Information

**ArXiv ID:** {paper_id}  
**Published:** {published_date}  
**Categories:** {', '.join(categories)}

## 👥 Authors

{chr(10).join([f"- {author}" for author in authors])}

## 📝 Abstract

{abstract}

## 🔗 Links

- **ArXiv Page:** [{arxiv_url}]({arxiv_url})
- **PDF Download:** [{pdf_url}]({pdf_url})

## 📚 Research Notes

See [research_notes.md](research_notes.md) for detailed analysis and notes.

## 🏷️ Topics and Keywords

{', '.join(categories)}

## 📊 Citation

```bibtex
@article{{{paper_id.replace('.', '')},
  title={{{title}}},
  author={{{' and '.join(authors)}}},
  journal={{arXiv preprint arXiv:{paper_id}}},
  year={{{published_date[:4]}}},
  url={{{arxiv_url}}}
}}
```

---

*This repository was automatically created by the MCP OAuth Research Assistant.*  
*Repository created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
    
    def _generate_metadata_file(
        self, title: str, paper_id: str, authors: List[str],
        abstract: str, pdf_url: str, arxiv_url: str,
        categories: List[str], published_date: str
    ) -> str:
        """Generate machine-readable metadata file"""
        import json
        
        metadata = {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published_date": published_date,
            "categories": categories,
            "urls": {
                "arxiv": arxiv_url,
                "pdf": pdf_url
            },
            "repository_created": datetime.now().isoformat(),
            "created_by": "MCP OAuth Research Assistant"
        }
        
        return json.dumps(metadata, indent=2)
    
    def _generate_notes_template(self, title: str) -> str:
        """Generate a research notes template"""
        return f"""# Research Notes: {title}

## 🎯 Key Contributions

*List the main contributions of this paper*

- 
- 
- 

## 🔬 Methodology

*Describe the methods used*

### Approach


### Experiments


### Datasets


## 📈 Results

*Summarize key findings*

### Main Results


### Performance Metrics


## 💭 Personal Analysis

*Your thoughts and analysis*

### Strengths


### Limitations


### Questions for Further Investigation


## 🔗 Related Work

*Papers and resources related to this work*

- 
- 
- 

## 📝 Implementation Notes

*Technical details for reproduction*

### Code Availability


### Dependencies


### Reproduction Steps


## 🏷️ Tags

*Add relevant tags for organization*

Tags: `research`, `paper-analysis`, `{title.lower().replace(' ', '-')}`

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}  
**Status:** 🔄 In Progress
"""
