import { useState } from "react";
function Card({ card }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <button
      className={`flashcard ${flipped ? "flipped" : ""}`}
      onClick={() => setFlipped((v) => !v)}
      aria-pressed={flipped}
    >
      <span className="flashcard-inner">
        <span className="flashcard-face" aria-hidden={flipped}>
          <strong className="text-xl">{card.term}</strong>
          <span className="mt-5 text-sm">Show answer ↻</span>
        </span>
        <span className="flashcard-face flashcard-back" aria-hidden={!flipped}>
          <span>{card.definition}</span>
          <span className="mt-5 text-sm">Show term ↻</span>
        </span>
      </span>
    </button>
  );
}
export function Flashcards({ cards }) {
  const [index, setIndex] = useState(0);
  return (
    <section>
      <p className="muted mb-4">
        Card {index + 1} of {cards.length}. Try recalling the answer before
        flipping.
      </p>
      <Card key={index} card={cards[index]} />
      <div className="mt-5 flex justify-between gap-4">
        <button
          className="btn-secondary"
          disabled={index === 0}
          onClick={() => setIndex((v) => v - 1)}
        >
          Previous card
        </button>
        <button
          className="btn-secondary"
          disabled={index === cards.length - 1}
          onClick={() => setIndex((v) => v + 1)}
        >
          Next card
        </button>
      </div>
    </section>
  );
}
function Question({ item, index }) {
  const [revealed, setRevealed] = useState(false),
    [answer, setAnswer] = useState("");
  return (
    <article className="panel">
      <h3 id={`question-${index}`}>
        {index + 1}. {item.question}
      </h3>
      {item.type === "multiple_choice" ? (
        <fieldset
          aria-labelledby={`question-${index}`}
          className="mt-4 space-y-3"
        >
          <legend className="sr-only">Choose an answer</legend>
          {item.options.map((option) => (
            <label className="flex items-start gap-3" key={option}>
              <input
                type="radio"
                className="mt-1"
                name={`question-${index}`}
                value={option}
                checked={answer === option}
                onChange={() => setAnswer(option)}
              />
              <span>{option}</span>
            </label>
          ))}
        </fieldset>
      ) : (
        <label className="field mt-4">
          Your answer
          <textarea
            rows={3}
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Try answering in your own words…"
          />
        </label>
      )}
      <button
        className="btn-secondary mt-4"
        aria-expanded={revealed}
        aria-controls={`answer-${index}`}
        onClick={() => setRevealed((v) => !v)}
      >
        {revealed ? "Hide answer" : "Reveal answer"}
      </button>
      <div
        hidden={!revealed}
        id={`answer-${index}`}
        className="notice-success mt-4"
      >
        <p className="font-semibold">Suggested answer</p>
        <p className="mt-2 whitespace-pre-wrap">{item.answer}</p>
        {item.type === "multiple_choice" && answer && (
          <p className="mt-2">
            {answer === item.answer
              ? "Your choice matches."
              : "Review the explanation and try again."}
          </p>
        )}
      </div>
    </article>
  );
}
export function Practice({ questions }) {
  return (
    <div className="space-y-5">
      {questions.map((q, i) => (
        <Question key={i} item={q} index={i} />
      ))}
    </div>
  );
}
