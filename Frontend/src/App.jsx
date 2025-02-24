import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import JobBoard from "./components/JobBoard";

function Home() {
  return <h1>Home Page</h1>;
}

function Startups() {
  return <h1>Startups Page</h1>;
}

function Advertise() {
  return <h1>Advertise Page</h1>;
}

function PostJob() {
  return <h1>Post a Job Page</h1>;
}

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        {/* <Route path="/" element={<Home />} /> */}
        <Route path="/startups" element={<Startups />} />
        <Route path="/advertise" element={<Advertise />} />
        <Route path="/post-job" element={<PostJob />} />
        <Route path="/" element={<JobBoard />} />
      </Routes>
    </Router>
  );
}

export default App;
