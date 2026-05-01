import { createDemoDatabase } from "./demo-data.js";

const db = createDemoDatabase();

console.log(
  JSON.stringify(
    {
      organizations: db.organizations.length,
      users: db.users.length,
      students: db.students.length,
      supportCases: db.supportCases.length,
      memoryCards: db.memoryCards.length,
      missionContents: db.missionContents.length,
      publicDataSources: db.publicDataSources.length,
    },
    null,
    2,
  ),
);
