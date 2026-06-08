"""Gradio query interface for The Unofficial Guide — Off-Campus Housing near Stevens.

Run:
    python app.py
then open http://localhost:7860

The UI shows the grounded answer and, separately, the source documents the answer was
drawn from (built programmatically in query.ask, not parsed from the model output).
"""

import gradio as gr

from query import ask

EXAMPLES = [
    "What do tenants say about flooding at the Hudson Tea Building?",
    "How do I minimize flood risk when renting in Hoboken?",
    "Is Uptown or Downtown Hoboken quieter and cheaper?",
    "Is Jersey City cheaper than Hoboken for a student?",
    "What are the complaints about management at 333 River Street?",
]


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources — answer not grounded in the documents)"
    return result["answer"], sources


with gr.Blocks(title="Unofficial Guide: Off-Campus Housing @ Stevens") as demo:
    gr.Markdown(
        "# Unofficial Guide: Off-Campus Housing near Stevens (Hoboken, NJ)\n"
        "Ask about apartments, neighborhoods, flooding, rent, broker fees, and landlords. "
        "Answers come only from collected reviews and guides — if the documents don't cover "
        "your question, the assistant will say so."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. How do I minimize flood risk when renting in Hoboken?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
