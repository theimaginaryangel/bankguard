// We are now pointing to the REAL API deployed in AWS!
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://rl46a80anl.execute-api.us-east-1.amazonaws.com/Prod";

export async function fetchSummary() {
  try {
    const res = await fetch(`${API_BASE_URL}/stats/summary`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("Error fetching summary:", err);
    return null;
  }
}

export async function fetchFindings(type: 'COMPLIANCE' | 'FRAUD') {
  try {
    const res = await fetch(`${API_BASE_URL}/findings?type=${type}`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error(`Error fetching ${type} findings:`, err);
    return [];
  }
}

export async function uploadFileSecurely(file: File) {
  try {
    // 1. Get the pre-signed POST "ticket" from our API
    const ticketRes = await fetch(`${API_BASE_URL}/upload-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name })
    });
    
    if (!ticketRes.ok) throw new Error("Failed to get upload ticket");
    
    const ticket = await ticketRes.json();
    
    // 2. Build the exact form data S3 expects
    const formData = new FormData();
    Object.entries(ticket.fields).forEach(([key, value]) => {
      formData.append(key, value as string);
    });
    // The file MUST be the absolute last thing in the form data!
    formData.append("file", file);
    
    // 3. Send the file directly to S3!
    const uploadRes = await fetch(ticket.url, {
      method: "POST",
      body: formData,
    });
    
    if (!uploadRes.ok) throw new Error("AWS S3 rejected the file!");
    
    return true;
  } catch (err) {
    console.error("Upload error:", err);
    return false;
  }
}
