"""Information extraction from ArXiv papers."""

import re
from typing import List
from rich.console import Console
from arxiv_research_demo.models import Paper, ExtractedInfo

console = Console()


class InformationExtractor:
    """Extracts key information from papers."""
    
    def extract_info(self, paper: Paper) -> ExtractedInfo:
        """Extract key information from a paper."""
        console.print(f"📋 Extracting info from: [bold]{paper.title[:50]}...[/bold]")
        
        abstract = paper.summary
        
        # Extract different types of information
        key_findings = self._extract_key_findings(abstract)
        methodology = self._extract_methodology(abstract)
        datasets_used = self._extract_datasets(abstract)
        limitations = self._extract_limitations(abstract)
        future_work = self._extract_future_work(abstract)
        
        return ExtractedInfo(
            title=paper.title,
            authors=paper.authors,
            key_findings=key_findings,
            methodology=methodology,
            datasets_used=datasets_used,
            limitations=limitations,
            future_work=future_work,
            paper_id=paper.paper_id,
            arxiv_url=f"https://arxiv.org/abs/{paper.paper_id}"
        )
    
    def _extract_key_findings(self, abstract: str) -> List[str]:
        """Extract key findings from abstract."""
        findings = []
        
        # Look for result indicators
        result_patterns = [
            r'[Ww]e (show|demonstrate|find|observe|achieve|improve|report|present) (that )?([^.]+)',
            r'[Oo]ur (results|experiments|analysis|study|findings) (show|demonstrate|indicate|reveal) (that )?([^.]+)',
            r'[Tt]his (work|paper|study|research) (shows|demonstrates|finds|achieves) (that )?([^.]+)',
            r'[Ww]e (obtain|achieve|reach|attain) ([^.]+)',
        ]
        
        for pattern in result_patterns:
            matches = re.finditer(pattern, abstract, re.IGNORECASE)
            for match in matches:
                # Extract the finding part (last group)
                finding = match.group(match.lastindex).strip()
                if finding and len(finding) > 10:  # Filter out very short findings
                    findings.append(finding)
        
        return findings[:3]  # Limit to top 3
    
    def _extract_methodology(self, abstract: str) -> str:
        """Extract methodology from abstract."""
        method_patterns = [
            r'[Ww]e (use|employ|apply|adopt|propose|develop|introduce) (a |an )?([^.]+method[^.]*)',
            r'[Oo]ur (approach|method|technique|framework|algorithm) ([^.]+)',
            r'[Ww]e (propose|present|introduce) (a |an )?([^.]+approach[^.]*)',
            r'[Tt]his (work|paper|study) (uses|employs|applies|proposes) ([^.]+)',
        ]
        
        for pattern in method_patterns:
            match = re.search(pattern, abstract, re.IGNORECASE)
            if match:
                # Extract the methodology part (last group)
                methodology = match.group(match.lastindex).strip()
                if methodology and len(methodology) > 10:
                    return methodology
        
        return "Methodology not clearly identified in abstract"
    
    def _extract_datasets(self, abstract: str) -> List[str]:
        """Extract datasets mentioned in abstract."""
        datasets = []
        
        # Look for common dataset patterns
        dataset_patterns = [
            r'([A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*)*)\s+dataset',
            r'dataset[s]?\s+([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+)*)',
            r'([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+)*)\s+corpus',
            r'([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+)*)\s+benchmark',
        ]
        
        for pattern in dataset_patterns:
            matches = re.finditer(pattern, abstract, re.IGNORECASE)
            for match in matches:
                dataset = match.group(1).strip()
                if dataset and len(dataset) > 2:
                    datasets.append(dataset)
        
        return list(set(datasets))[:3]  # Remove duplicates and limit
    
    def _extract_limitations(self, abstract: str) -> List[str]:
        """Extract limitations mentioned in abstract."""
        limitations = []
        
        limitation_patterns = [
            r'[Ll]imitation[s]?\s+([^.]+)',
            r'[Hh]owever,\s+([^.]+)',
            r'[Nn]evertheless,\s+([^.]+)',
            r'[Dd]espite\s+([^.]+)',
            r'[Aa]lthough\s+([^.]+)',
        ]
        
        for pattern in limitation_patterns:
            matches = re.finditer(pattern, abstract)
            for match in matches:
                limitation = match.group(1).strip()
                if limitation and len(limitation) > 10:
                    limitations.append(limitation)
        
        return limitations[:2]  # Limit to top 2
    
    def _extract_future_work(self, abstract: str) -> List[str]:
        """Extract future work mentions from abstract."""
        future_work = []
        
        future_patterns = [
            r'[Ff]uture work\s+([^.]+)',
            r'[Ff]uture research\s+([^.]+)',
            r'[Ff]uture studies\s+([^.]+)',
            r'[Nn]ext steps?\s+([^.]+)',
            r'[Ww]e plan to\s+([^.]+)',
        ]
        
        for pattern in future_patterns:
            matches = re.finditer(pattern, abstract)
            for match in matches:
                future = match.group(1).strip()
                if future and len(future) > 10:
                    future_work.append(future)
        
        return future_work[:2]  # Limit to top 2
