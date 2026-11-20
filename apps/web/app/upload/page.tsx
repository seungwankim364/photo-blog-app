import UploadForm from "./UploadForm";

export default function UploadPage() {
  return (
    <main>
      <h1 style={{ fontSize: "1.25rem" }}>Upload photos</h1>
      <p className="muted">JPEG, HEIC or PNG. Camera details are read from each file.</p>
      <UploadForm />
    </main>
  );
}
