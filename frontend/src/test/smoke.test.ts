import { describe, it, expect } from "vitest";

describe("Frontend Environment Setup", () => {
  it("executes basic assertions cleanly", () => {
    expect(1 + 1).toBe(2);
  });

  it("has DOM window and document defined", () => {
    expect(window).toBeDefined();
    expect(document).toBeDefined();
    const element = document.createElement("div");
    element.textContent = "ResearchAI";
    document.body.appendChild(element);
    expect(element).toHaveTextContent("ResearchAI");
  });
});
