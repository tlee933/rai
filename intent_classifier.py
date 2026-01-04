#!/usr/bin/env python3
"""
F3D0R4 Intent Classifier
Fast pattern matching for common intents with LLM fallback
"""

import re
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class Intent:
    """Represents a classified user intent"""
    category: str  # e.g., 'gpu', 'git', 'file', 'system', 'llm'
    action: str    # e.g., 'stats', 'status', 'read', 'info'
    params: Dict[str, Any]


class IntentClassifier:
    """
    Fast intent classification using regex patterns
    Falls back to LLM for complex queries
    """

    # Pattern format: (pattern, category, action, param_extractor)
    PATTERNS = [
        # GPU/ROCm queries - Order matters! More specific patterns first

        # VRAM-specific queries
        (r'^(?:show|get|check)[\s-]*(?:gpu[\s-]*)?vram(?:[\s-]*(?:usage|stats?))?$',
         'gpu', 'vram', lambda m: {}),

        (r'^vram$',
         'gpu', 'vram', lambda m: {}),

        # Temperature-specific queries
        (r'^(?:gpu|show|get|check)[\s-]*temp(?:erature)?$',
         'gpu', 'temp', lambda m: {}),

        # General GPU stats (catch-all)
        (r'^(?:gpu|rocm)[\s-]*(?:stats?|status|info)$',
         'gpu', 'stats', lambda m: {}),

        (r'^(?:show|get|check)[\s-]*(?:gpu|rocm)(?:[\s-]*(?:stats?|status|info))?$',
         'gpu', 'stats', lambda m: {}),

        # Git operations
        (r'^git[\s-]+(status|st|diff|log)$',
         'git', lambda m: m.group(1), lambda m: {}),

        (r'^(?:show|check)[\s-]*(?:git[\s-]*)?(?:status|changes|diff)$',
         'git', 'status', lambda m: {}),

        (r'^git[\s-]+commit[\s-]+-m[\s-]+"([^"]+)"$',
         'git', 'commit', lambda m: {'message': m.group(1)}),

        # Atomic Desktop queries (rpm-ostree, Flatpak, toolbox) - Before file ops!
        (r'^(?:show|get|check)[\s-]*(?:rpm-?ostree|ostree)[\s-]*(?:status)?$',
         'atomic', 'ostree_status', lambda m: {}),

        (r'^(?:ostree|rpm-?ostree)[\s-]*status$',
         'atomic', 'ostree_status', lambda m: {}),

        (r'^(?:check|show)[\s-]*(?:system[\s-]*)?updates?$',
         'atomic', 'check_updates', lambda m: {}),

        (r'^(?:rpm-?ostree|ostree)[\s-]*(?:check|show)[\s-]*updates?$',
         'atomic', 'check_updates', lambda m: {}),

        (r'^(?:show|list|get)[\s-]*layered[\s-]*packages?$',
         'atomic', 'layered_packages', lambda m: {}),

        (r'^(?:show|list|get)[\s-]*flatpaks?(?:[\s-]*apps?)?$',
         'atomic', 'flatpaks', lambda m: {}),

        (r'^(?:check|show)[\s-]*flatpak[\s-]*updates?$',
         'atomic', 'flatpak_updates', lambda m: {}),

        (r'^(?:show|list|get)[\s-]*toolbox(?:es)?$',
         'atomic', 'toolboxes', lambda m: {}),

        (r'^(?:show|list|get)[\s-]*(?:distrobox|toolbox)[\s-]*(?:containers?|list)?$',
         'atomic', 'toolboxes', lambda m: {}),

        # File operations
        (r'^(?:read|show|cat)[\s-]+(?:file[\s-]+)?(.+)$',
         'file', 'read', lambda m: {'path': m.group(1).strip()}),

        (r'^(?:write|create)[\s-]+(?:file[\s-]+)?(.+)$',
         'file', 'write', lambda m: {'path': m.group(1).strip()}),

        (r'^(?:list|ls)[\s-]+(.+)$',
         'file', 'list', lambda m: {'path': m.group(1).strip()}),

        (r'^(?:find|search)[\s-]+(?:for[\s-]+)?(.+?)(?:[\s-]+in[\s-]+(.+))?$',
         'file', 'search', lambda m: {
             'pattern': m.group(1).strip(),
             'path': m.group(2).strip() if m.group(2) else '.'
         }),

        # System queries
        (r'^(?:show|get|check)[\s-]*(?:mem|memory|ram)(?:[\s-]*usage)?$',
         'system', 'memory', lambda m: {}),

        (r'^(?:show|get|check)[\s-]*(?:disk|space|storage)(?:[\s-]*usage)?$',
         'system', 'disk', lambda m: {}),

        (r'^(?:systemctl|service)[\s-]+status[\s-]+(.+)$',
         'system', 'service_status', lambda m: {'service': m.group(1).strip()}),

        (r'^(?:check|is)[\s-]+(.+?)[\s-]+(?:running|active)$',
         'system', 'service_status', lambda m: {'service': m.group(1).strip()}),

        (r'^(?:show|get|check)[\s-]*(?:system|systemd)?[\s-]*(?:logs?|journal)(?:[\s-]*(?:for|from))?[\s-]*(.*)$',
         'system', 'logs', lambda m: {'filter': m.group(1).strip() if m.group(1) else None}),

        (r'^(?:list|show)[\s-]*(?:all[\s-]*)?services$',
         'system', 'list_services', lambda m: {}),

        (r'^(?:show|get|check|list)[\s-]*(?:processes?|procs?)(?:[\s-]*list)?$',
         'system', 'processes', lambda m: {}),

        # Build operations
        (r'^(?:build|compile|make)(?:[\s-]+(.+))?$',
         'build', 'ninja', lambda m: {'target': m.group(1).strip() if m.group(1) else 'all'}),

        (r'^cmake[\s-]+(.+)$',
         'build', 'cmake', lambda m: {'args': m.group(1).strip()}),

        # Package queries
        (r'^(?:is|check)[\s-]+(.+?)[\s-]+installed$',
         'package', 'check', lambda m: {'package': m.group(1).strip()}),

        (r'^pip[\s-]+show[\s-]+(.+)$',
         'package', 'info', lambda m: {'package': m.group(1).strip()}),

        # Process queries
        (r'^(?:show|list|ps)[\s-]*(?:processes?)?(?:[\s-]+(.+))?$',
         'process', 'list', lambda m: {'filter': m.group(1).strip() if m.group(1) else None}),

        # Network queries
        (r'^(?:port|check)[\s-]+(\d+)$',
         'network', 'port_check', lambda m: {'port': int(m.group(1))}),

        # Note: Removed calc pattern - LLM handles math queries better
    ]

    def __init__(self):
        # Compile patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), category, action, extractor)
            for pattern, category, action, extractor in self.PATTERNS
        ]

    def classify(self, query: str) -> Optional[Intent]:
        """
        Classify user query into an intent
        Returns None if no pattern matches (use LLM fallback)
        """
        query = query.strip()

        for pattern, category, action, extractor in self.compiled_patterns:
            match = pattern.match(query)
            if match:
                # Resolve action if it's a lambda
                resolved_action = action(match) if callable(action) else action

                # Extract parameters
                params = extractor(match)

                return Intent(
                    category=category,
                    action=resolved_action,
                    params=params
                )

        return None

    def should_use_llm(self, query: str) -> bool:
        """
        Determine if query needs LLM processing
        Fast patterns handle simple queries, LLM handles complex ones
        """
        intent = self.classify(query)
        return intent is None


def test_classifier():
    """Test the intent classifier"""
    classifier = IntentClassifier()

    test_cases = [
        "gpu stats",
        "show gpu vram",
        "git status",
        "read /tmp/test.txt",
        "find python files in /home",
        "is llama-server running",
        "build rocm",
        "what is 15 factorial",
        "explain how async works in Python",  # Should return None (LLM)
    ]

    print("Intent Classification Tests")
    print("=" * 70)

    for query in test_cases:
        intent = classifier.classify(query)
        if intent:
            print(f"\nQuery: {query}")
            print(f"  Category: {intent.category}")
            print(f"  Action:   {intent.action}")
            print(f"  Params:   {intent.params}")
            print(f"  Use LLM:  No")
        else:
            print(f"\nQuery: {query}")
            print(f"  Use LLM:  Yes (no pattern match)")


if __name__ == "__main__":
    test_classifier()
