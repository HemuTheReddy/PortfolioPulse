"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitQuiz, getRecommendations, getMarketState, getApiErrorMessage } from "@/lib/api";

const QUESTIONS = [
    {
        key: "horizon",
        title: "What's your investment time horizon?",
        subtitle: "How long do you plan to hold your crypto portfolio?",
        options: [
            { key: "<1m", label: "Less than 1 month" },
            { key: "1-6m", label: "1 – 6 months" },
            { key: "6m-2y", label: "6 months – 2 years" },
            { key: "2y+", label: "2+ years" },
        ],
    },
    {
        key: "loss",
        title: "If your portfolio dropped 40% overnight…",
        subtitle: "What would you most likely do?",
        options: [
            { key: "sell_all", label: "Sell everything" },
            { key: "sell_some", label: "Sell some to cut losses" },
            { key: "hold", label: "Hold and wait" },
            { key: "buy_more", label: "Buy the dip" },
        ],
    },
    {
        key: "experience",
        title: "How long have you been in crypto?",
        subtitle: "Your experience helps us calibrate risk.",
        options: [
            { key: "never", label: "Brand new" },
            { key: "<1y", label: "Less than 1 year" },
            { key: "1-3y", label: "1 – 3 years" },
            { key: "3y+", label: "3+ years" },
        ],
    },
    {
        key: "volatility",
        title: "How do you feel about extreme volatility?",
        subtitle: "Crypto regularly swings 20–50%.",
        options: [
            { key: "very_uncomfortable", label: "Very uncomfortable" },
            { key: "somewhat", label: "Somewhat uneasy" },
            { key: "neutral", label: "Neutral" },
            { key: "comfortable", label: "Comfortable" },
        ],
    },
    {
        key: "capital",
        title: "What % of your net worth is this portfolio?",
        subtitle: "This helps us set appropriate risk limits.",
        options: [
            { key: "<5pct", label: "Less than 5%" },
            { key: "5-15", label: "5 – 15%" },
            { key: "15-30", label: "15 – 30%" },
            { key: "30plus", label: "30%+" },
        ],
    },
    {
        key: "goal",
        title: "What's your primary investment goal?",
        subtitle: "Choose the objective closest to yours.",
        options: [
            { key: "preserve", label: "Capital preservation" },
            { key: "steady", label: "Steady growth" },
            { key: "aggressive", label: "Aggressive growth" },
            { key: "speculation", label: "High-risk speculation" },
        ],
    },
];

export default function QuizPage() {
    const router = useRouter();
    const [step, setStep] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const current = QUESTIONS[step];
    const progress = ((step + 1) / QUESTIONS.length) * 100;

    const selectAnswer = (answerKey: string) => {
        if (errorMessage) setErrorMessage("");
        setAnswers((prev) => ({ ...prev, [current.key]: answerKey }));
    };

    const next = async () => {
        if (step < QUESTIONS.length - 1) {
            setStep(step + 1);
            return;
        }

        // Final question — submit
        setLoading(true);
        try {
            const quizResult = await submitQuiz(answers);
            const marketData = await getMarketState();
            const recs = await getRecommendations(
                quizResult.proxy_user.user_idx,
                quizResult.risk_score,
                marketData.market_state
            );

            // Store in sessionStorage for results page
            sessionStorage.setItem(
                "portfoliopulse_results",
                JSON.stringify({
                    quiz: quizResult,
                    market: marketData,
                    recommendations: recs,
                })
            );

            router.push("/results");
        } catch (err: unknown) {
            setErrorMessage(getApiErrorMessage(err));
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
                <p>Analyzing your profile & generating recommendations…</p>
            </div>
        );
    }

    return (
        <div className="quiz-container">
            <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>

            <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 24 }}>
                Question {step + 1} of {QUESTIONS.length}
            </p>

            <h2 className="quiz-question">{current.title}</h2>
            <p className="quiz-subtitle">{current.subtitle}</p>

            <div className="quiz-options">
                {current.options.map((opt) => (
                    <button
                        key={opt.key}
                        className={`quiz-tile${answers[current.key] === opt.key ? " selected" : ""}`}
                        onClick={() => selectAnswer(opt.key)}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            <div className="quiz-nav">
                {step > 0 && (
                    <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
                        ← Back
                    </button>
                )}
                <button
                    className="btn btn-primary"
                    disabled={!answers[current.key]}
                    onClick={next}
                    style={{ opacity: answers[current.key] ? 1 : 0.4 }}
                >
                    {step < QUESTIONS.length - 1 ? "Next →" : "Get Recommendations →"}
                </button>
            </div>
            {errorMessage && (
                <p style={{ marginTop: 12, color: "#FF6B6B", fontSize: 13 }}>{errorMessage}</p>
            )}
        </div>
    );
}
