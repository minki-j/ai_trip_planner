import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { client } from "@/lib/mongodb";
import { ObjectId } from "mongodb";

export async function DELETE(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const db = client.db("test");
    const collection = db.collection('results');

    const result = await collection.findOne({
      _id: new ObjectId(params.id),
      userId: session.user?.id,
    });

    if (!result) {
      return new NextResponse("Document not found", { status: 404 });
    }

    await collection.deleteOne({ _id: new ObjectId(params.id) });

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("[DELETE]", error);
    return new NextResponse("Internal Error", { status: 500 });
  }
}