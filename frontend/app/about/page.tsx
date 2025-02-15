"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Github, Globe } from "lucide-react";
import { motion } from "framer-motion";

const AboutPage = () => {
  return (
    <div className="min-h-screen from-background to-muted flex flex-col bg-gradient-to-b from-background to-muted/50">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex-grow flex flex-col items-center justify-center px-4 py-16 sm:px-6 lg:px-8"
      >
        <div className="text-center max-w-xl mx-auto backdrop-blur-sm bg-background/50 p-8 rounded-xl shadow-lg border border-border/50">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="font-bold text-2xl md:text-3xl text-primary mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/80"
          >
            Built by Minki Jung
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mb-8 text-muted-foreground text-lg"
          >
            For more information,
            <br />
            visit my blog or github page.
          </motion.p>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex justify-center space-x-6"
          >
            <Button
              variant="outline"
              className="flex items-center gap-2 px-6 py-5 hover:scale-105 transition-transform duration-200 hover:bg-primary/5 hover:border-primary/30"
            >
              <Globe className="h-5 w-5" />
              <a
                href="https://minkijung.notion.site/Hey-I-m-Minki-140a2fb3932580be9235ca65b1306b0d"
                target="_blank"
                rel="noopener noreferrer"
                className="no-underline font-medium"
              >
                Blog
              </a>
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2 px-6 py-5 hover:scale-105 transition-transform duration-200 hover:bg-primary/5 hover:border-primary/30"
            >
              <Github className="h-5 w-5" />
              <a
                href="https://github.com/minki-j/ai_tour_assistant"
                target="_blank"
                rel="noopener noreferrer"
                className="no-underline font-medium"
              >
                GitHub
              </a>
            </Button>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default AboutPage;
