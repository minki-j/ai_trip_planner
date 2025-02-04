import { revalidatePath } from 'next/cache';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get('path');

  if (!path) {
    return NextResponse.json(
      { message: 'Missing path parameter' },
      { status: 400 }
    );
  }

  try {
    revalidatePath(path, 'page');

    return NextResponse.json({ revalidated: true, now: Date.now() });
  } catch (err) {
    console.error('Error revalidating:', err);
    return NextResponse.json(
      { message: 'Error revalidating', error: err },
      { status: 500 }
    );
  }
}
