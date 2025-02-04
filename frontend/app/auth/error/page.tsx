'use client';

import { useSearchParams } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { redirect } from "next/navigation";


export default function ErrorPage() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error');
  const [email, setEmail] = useState('');
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/error-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ error, email }),
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      setEmailSent(true);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <Card className="w-full max-w-md p-8 bg-white">
        {emailSent ? <div className="flex flex-col space-y-6">
          <p style={{ color: "black" }} className="text-center ">Email sent successfully. You can try the app without logging in for now.</p>
          <Button variant="secondary" onClick={async () => {
            await signIn("temporary").then(() => {
              redirect("/");
            });
          }}>Try the app</Button>
        </div> : <div className="space-y-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Sorry, something went wrong.</AlertTitle>
            <AlertDescription>
              Please leave your email here, we will reach out to you when the error is fixed.
            </AlertDescription>
          </Alert>
          <div className="space-x-2 flex items-center">
            <Input type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button variant="secondary" onClick={handleSubmit}>Submit</Button>
          </div>
        </div>
        }
      </Card>
    </div>
  );
}
