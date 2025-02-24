"use client"

import { Clock, MapPin, Search, Signal, ChevronDown } from "lucide-react"
import { Link } from "react-router-dom";

export default function JobBoard() {
    return (
        <main className="mx-auto max-w-7xl px-4 py-8">
            {/* Header Section */}
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-blue-600">
                    <Link to="/remote-startup-jobs">Remote startup jobs.</Link>
                </h1>
                <p className="mt-2 text-2xl text-gray-900">
                    Help shape the future by joining one of the fastest growing technology startups.
                </p>
            </div>

            {/* Search Section */}
            <div className="mb-8 rounded-lg border border-gray-200 p-4">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Keywords..."
                            className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    <div className="relative">
                        <MapPin className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Remote only"
                            className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                </div>

                <div className="mt-4 flex items-center gap-2">
                    <button className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                        <Signal className="h-4 w-4" />
                        Remote only
                    </button>
                    <button className="flex items-center gap-2 rounded-md border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
                        Type
                        <ChevronDown className="h-4 w-4" />
                    </button>
                    <button className="flex items-center gap-2 rounded-md border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
                        Anytime
                        <ChevronDown className="h-4 w-4" />
                    </button>
                    <div className="ml-auto text-sm text-gray-500">
                        Search by
                        <img
                            src="https://www.algolia.com/images/shared/algolia-logo-light.svg"
                            alt="Algolia"
                            className="ml-2 inline-block h-4"
                        />
                    </div>
                </div>
            </div>

            {/* Job Listings */}
            <div className="space-y-4">
                {[
                    {
                        logo: "A",
                        company: "Aquila",
                        title: "Photovoltaics Materials Engineer",
                        tags: ["Engineer"],
                        timeAgo: "2 weeks ago",
                    },
                    {
                        logo: "C",
                        company: "Credo",
                        title: "Customer Success Manager",
                        tags: ["Exec", "Support"],
                        timeAgo: "4 weeks ago",
                    },
                    {
                        logo: "CW",
                        company: "Closer Work",
                        title: "CEO Americas, Management Consulting and Services Group, Healthcare",
                        tags: ["CEO", "Exec", "Consulting"],
                        timeAgo: "4 weeks ago",
                    },
                ].map((job, index) => (
                    <div
                        key={index}
                        className="flex items-center justify-between rounded-lg border border-gray-200 p-4 hover:border-gray-300"
                    >
                        <div className="flex items-center gap-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-md bg-gray-900 text-white">
                                {job.logo}
                            </div>
                            <div>
                                <h3 className="font-medium">{job.title}</h3>
                                <div className="flex items-center gap-2 text-sm text-gray-500">
                                    <span>{job.company}</span>
                                    <span className="flex items-center gap-1">
                                        <Signal className="h-3 w-3" />
                                        REMOTE
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {job.timeAgo}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {job.tags.map((tag, tagIndex) => (
                                <span key={tagIndex} className="rounded-md border border-gray-200 px-3 py-1 text-sm">
                                    {tag}
                                </span>
                            ))}
                            <button className="ml-4 rounded-md border border-gray-300 px-4 py-1 text-sm font-medium hover:bg-gray-50">
                                Apply
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </main>
    )
}

