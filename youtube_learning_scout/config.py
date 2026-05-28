"""Small knobs for credibility checks.

Keep this list short. The goal is to nudge rankings toward official or
high-credibility sources when they appear, not to maintain a channel database.
"""

OFFICIAL_CHANNEL_NAMES = {
    "anthropic",
    "openai",
    "google for developers",
    "microsoft developer",
    "aws developers",
    "ibm technology",
    "deeplearning.ai",
    "freecodecamp.org",
}

IMPLEMENTATION_STEP_TERMS = {
    "install",
    "clone",
    "run",
    "configure",
    "api key",
    "environment variable",
    "terminal",
    "command",
    "python",
    "npm",
    "pip",
    "code",
    "build",
    "deploy",
}

HYPE_TERMS = {
    "secret",
    "insane",
    "easy money",
    "get rich",
    "guaranteed",
    "shocking",
    "you won't believe",
    "changed my life",
}
