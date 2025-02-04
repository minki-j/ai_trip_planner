import { NextResponse } from 'next/server';
import { client } from '@/lib/mongodb';

export async function POST(request: Request) {
    const body = await request.json();
    const { error, email } = body;

    if (!error || !email) {
        return NextResponse.json({ message: 'Error and email are required.' }, { status: 400 });
    }

    try {
        const db = client.db("test");
        await db.collection('error_report').insertOne({
            error,
            email,
            timestamp: new Date() 
        });

        return NextResponse.json({ message: 'Error reported successfully.' }, { status: 200 });
    } catch (error) {
        return NextResponse.json({ message: 'Failed to report error.', error: error }, { status: 500 });
    }
}