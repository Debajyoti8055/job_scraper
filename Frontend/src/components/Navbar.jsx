"use client"

import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
    const [isOpen, setIsOpen] = useState({
        browse: false,
        more: false,
        employers: false,
    })

    return (
        <nav className="w-full border-b border-gray-200 bg-white px-4 py-3">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
                {/* Logo */}
                <Link to="/" className="shrink-0">
                    <img
                        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-PXpND0TFrAi414MNAJ99WVQFQY6V1V.png"
                        alt="Logo"
                        className="h-8 w-8"
                    />
                </Link>

                {/* Navigation Links */}
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <button
                            onClick={() => setIsOpen({ ...isOpen, browse: !isOpen.browse })}
                            className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
                        >
                            Browse Jobs
                            <ChevronDown className="h-4 w-4" />
                        </button>
                    </div>

                    <Link to="/startups" className="rounded-md px-3 py-1.5 text-sm hover:bg-gray-50">
                        Startups
                    </Link>

                    <Link to="/advertise" className="rounded-md px-3 py-1.5 text-sm hover:bg-gray-50">
                        Advertise
                    </Link>

                    <div className="relative">
                        <button
                            onClick={() => setIsOpen({ ...isOpen, more: !isOpen.more })}
                            className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
                        >
                            More
                            <ChevronDown className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="flex-1">
                    <input
                        type="search"
                        placeholder="Search jobs..."
                        className="w-full rounded-md border border-gray-300 px-4 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                </div>

                {/* Right Side */}
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <button
                            onClick={() => setIsOpen({ ...isOpen, employers: !isOpen.employers })}
                            className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
                        >
                            For Employers
                            <ChevronDown className="h-4 w-4" />
                        </button>
                    </div>

                    <Link
                        to="/post-job"
                        className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                    >
                        Post a job for ₹299
                    </Link>
                </div>
            </div>
        </nav>
    )
}

