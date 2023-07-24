#!/usr/bin/env node
// Sublime Text syntax highlighting: JavaScript

import { OpenAIPostGenerator } from 'julius-gpt'
import fs from 'fs';
import path from 'path';
import { retrieveDocuments } from './retrieve_documents.mjs';

// Access command-line arguments
const args = process.argv.slice(2);

// Print the arguments
console.log('Arguments:', args);

// Use the arguments
if (args.length < 2) {
  console.log('Please provide at least 2 arguments.');
}
const directory = args[0];
const subject = args[1];
const categories = JSON.stringify(args[2].split(','));
const topic = args[3];
const serp_outlines = args[4];
const vector_store = args[5];
  
console.log('Directory:', directory);
console.log('Subject:', subject);
console.log('Categories:', categories);
console.log('Topic:', topic);
console.log('Vector store:', vector_store);


const enrichOutline = async (outline, subject) => {
  console.log('ENRICHING');
  for (const heading of outline.headings) {
    if (heading.keywords && !['Conclusion', 'Introduction'].includes(heading.title)) {
      const query = `${heading.title} ${heading.keywords.join(', ')}`;

      heading.context = await retrieveDocuments(query, vector_store);
      if (heading.headings && heading.headings.length > 0) {
        for (const subheading of heading.headings) {
          const query = `${subheading.title} ${subheading.keywords.join(', ')}`;
          subheading.context = await retrieveDocuments(query, vector_store);
        }
      }
    }
  }
  return outline;
};

const prompt = {
  apiKey: process.env.OPENAI_KEY,
  topic: topic,
  enrichOutline: enrichOutline,
  serp_outlines: serp_outlines,
  withConclusion: true,
  model: 'gpt-3.5-turbo',
  audience: 'The audience are people interested in ' + subject, // optional
  language: 'english', // could be any language supported by GPT-4
  tone: null,
  intent: null,
  country: null,
  frequencyPenalty: 1, // optional
  presencePenalty: 1, // optional
  // temperature: 0.8, // optional
  // logitBias: 0, // optional
  debug: true, // optional
  debugapi: true, // optional
}

// console.log(prompt)

const postGenerator = new OpenAIPostGenerator(prompt)
const post = await postGenerator.generate()

const timestamp = new Date().toISOString().replace(/:/g, '-'); // Generate the current date and time as a valid timestamp
const date = timestamp.substr(0, 10);

const fileString = `---
title: "${post.title}"
date: "${date}"
description: "${post.seoDescription}"
categories: ${categories}
draft: false
slug: "${post.slug}"
---
${post.content}
`;

console.log(fileString)

const lowercaseKeyword = post.slug.toLowerCase().replace(/\s/g, '_'); // Convert the keyword to lowercase and replace spaces with underscores
const fileName = `${lowercaseKeyword}.${timestamp}.md`; // Construct the file name
const filePath = path.join(directory, fileName);

fs.writeFile(filePath, fileString, 'utf8', (err) => {
  if (err) {
    console.error('Error writing file:', err);
    return;
  }
  console.log('Markdown file has been written.');
});