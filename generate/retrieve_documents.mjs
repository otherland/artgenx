import fetch from 'node-fetch';

const apiUrl = 'http://localhost:5000/query';
export async function retrieveDocuments(query, directory) {
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, directory })
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    console.log(data);
    return data;
  } catch (error) {
    console.error('Error:', error.message);
  }
}

//retrieveDocuments('how to conserve water?', '/Users/admin/artgen/artgen/permaculture_vectors');
