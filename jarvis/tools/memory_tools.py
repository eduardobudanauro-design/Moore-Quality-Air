"""
Memory tools — let Jarvis read and write durable facts during a conversation.

These give the model agency over its own long-term memory:
  remember_fact    — store something Eduardo said or that Jarvis learned
  recall_facts     — look up what Jarvis knows about a topic
  update_fact      — correct a stale or wrong fact
  forget_fact      — remove a fact that's no longer true

Facts are written as plain statements, not commands.
They live in memory/facts.json — human-readable and directly editable.
"""

from tools import tool
import memory


@tool(
    name="remember_fact",
    description=(
        "Permanently remember something about Eduardo, his business, or his preferences. "
        "Use this when Eduardo tells you something worth keeping across sessions — his name, "
        "a preference, a goal, a decision, a key fact about his business. "
        "Write the fact as a clear, standalone statement. "
        "Category examples: identity, preference, business, goal, contact, project."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The fact to remember, written as a plain statement. E.g. 'Eduardo prefers morning meetings.'",
            },
            "category": {
                "type": "string",
                "description": "Category: identity, preference, business, goal, contact, project, or general.",
            },
        },
        "required": ["content"],
    },
)
def remember_fact(content: str, category: str = "general") -> str:
    fact = memory.add_fact(content, category)
    return f"Got it — remembered: \"{content}\" (#{fact['id']}, {category})"


@tool(
    name="recall_facts",
    description=(
        "Search what Jarvis already knows about a topic, person, or subject. "
        "Use this when Eduardo asks 'do you remember...', 'what do you know about...', "
        "or when context from past sessions would improve the answer."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keyword or topic to search for in stored facts.",
            },
        },
        "required": ["query"],
    },
)
def recall_facts(query: str) -> str:
    results = memory.search_facts(query)
    if not results:
        return f"Nothing stored about '{query}' yet."
    lines = [f"#{f['id']} [{f.get('category','general')}] {f['content']}" for f in results]
    return "\n".join(lines)


@tool(
    name="update_fact",
    description=(
        "Correct or update a fact Jarvis has stored. Use when Eduardo says something "
        "has changed or a stored fact is wrong. Requires the fact's ID number "
        "(use recall_facts to find it first if needed)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "fact_id": {
                "type": "integer",
                "description": "ID of the fact to update.",
            },
            "new_content": {
                "type": "string",
                "description": "The corrected fact, written as a plain statement.",
            },
        },
        "required": ["fact_id", "new_content"],
    },
)
def update_fact_tool(fact_id: int, new_content: str) -> str:
    result = memory.update_fact(fact_id, new_content)
    if result is None:
        return f"No fact found with ID {fact_id}."
    return f"Updated fact #{fact_id}: \"{new_content}\""


@tool(
    name="forget_fact",
    description=(
        "Delete a stored fact that is no longer true or no longer needed. "
        "Use when Eduardo explicitly says to forget something, or when a fact "
        "has been superseded and keeping it would cause confusion."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "fact_id": {
                "type": "integer",
                "description": "ID of the fact to delete.",
            },
        },
        "required": ["fact_id"],
    },
)
def forget_fact(fact_id: int) -> str:
    success = memory.delete_fact(fact_id)
    if not success:
        return f"No fact found with ID {fact_id}."
    return f"Forgot fact #{fact_id}."
