import { MongoClient, ServerApiVersion } from "mongodb";

const uri = process.env.MONGODB_URI
if (!uri) {
  throw new Error("MONGODB_URI is not set");
}


export const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
});

export async function connectDB() {
  try {
    if (!client.connect) return;
    await client.connect();
    await client.db("admin").command({ ping: 1 });
  } catch (error) {
    console.error("Error connecting to MongoDB:", error);
    throw error;
  }
}
