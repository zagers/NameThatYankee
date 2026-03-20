import {
  assertSucceeds,
  assertFails,
  initializeTestEnvironment,
} from "@firebase/rules-unit-testing";
import { readFileSync } from "fs";
import { describe, it, beforeAll, beforeEach } from "vitest";

let testEnv;

describe("Firestore Security Rules", () => {
  beforeAll(async () => {
    // Load your local rules file
    const rules = readFileSync("firestore.rules", "utf8");
    testEnv = await initializeTestEnvironment({
      projectId: "name-that-yankee-test",
      firestore: { rules },
    });
  });

  beforeEach(async () => {
    await testEnv.clearFirestore();
  });

  it("should allow creating a valid guess", async () => {
    const alice = testEnv.unauthenticatedContext();
    await assertSucceeds(
      alice.firestore().collection("guesses").add({
        guessText: "Derek Jeter",
        puzzleDate: "2026-03-20",
        timestamp: new Date(), // Mock serverTimestamp
      })
    );
  });

  it("should block a guess with missing fields", async () => {
    const malicious = testEnv.unauthenticatedContext();
    await assertFails(
      malicious.firestore().collection("guesses").add({
        guessText: "Derek Jeter",
        // missing puzzleDate and timestamp
      })
    );
  });

  it("should block a guess with an invalid date format", async () => {
    const malicious = testEnv.unauthenticatedContext();
    await assertFails(
      malicious.firestore().collection("guesses").add({
        guessText: "Derek Jeter",
        puzzleDate: "March 20th, 2026", // Wrong format
        timestamp: new Date(),
      })
    );
  });

  it("should block a guess that is too long (storage abuse)", async () => {
    const malicious = testEnv.unauthenticatedContext();
    await assertFails(
      malicious.firestore().collection("guesses").add({
        guessText: "A".repeat(101), // Over 100 limit
        puzzleDate: "2026-03-20",
        timestamp: new Date(),
      })
    );
  });

  it("should allow listing the collection for analytics", async () => {
    const visitor = testEnv.unauthenticatedContext();
    await assertSucceeds(visitor.firestore().collection("guesses").get());
  });

  it("should block direct access to a specific document (get)", async () => {
    const visitor = testEnv.unauthenticatedContext();
    await assertFails(
      visitor.firestore().collection("guesses").doc("some_id").get()
    );
  });
});
