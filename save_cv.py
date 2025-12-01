"""Save CV to Supabase"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

CV_TEXT = """Craig Haywood

LinkedIn CV

I open doors & close deals | Driving Sales Growth in Construction & Property | New Homes - Real Estate - High-Performance Building Products | Innovation-Driven, Design + Specification-Led Sales Leader

About
Hi, I'm Craig. I specialise in driving sales growth across the construction and property sectors by opening doors, building strong relationships, and turning opportunities into revenue and long-term partnerships.

People engage me for my ability to connect quickly, build trust fast, and convert momentum into results.

My background spans architectural design, new home sales, building products, and remote delivery teams - giving me a practical, design-led approach that resonates with builders, developers, consultants, and merchant channels.

Over the last few years I've delivered 750+ projects while leading teams across NZ and the Philippines, consistently turning technical conversations into commercially successful outcomes.

What I bring:
- Established relationships across builders, group home companies, merchants & consultants
- Hands-on industry experience - I understand the work, not just the pitch
- Ability to influence decisions and lead value-driven sales cycles
- Design + technical credibility when speaking with specifiers, engineers & councils
- Comfortable operating independently and growing a region or market from scratch
- A closer's mindset - move opportunities forward and get deals over the line
- Deep experience in high-performance panel systems, SIPs, and building envelope detailing

What excites me:
- New homes & modular construction
- Construction tech / SaaS (innovation-focused)
- Building products & merchant channels
- Real estate - new builds or existing homes
- High-performance solutions, airtightness & energy-efficient building envelopes

Experience

Business Owner / Director / Sales & Design Lead
XDD Xpress Design + Drafting | Nov 2017 - Present | Christchurch

- Built and led a hybrid NZ-Philippines architectural delivery team, scaling remote production capacity while reducing resourcing costs and turnaround times.
- Delivered 750+ residential, commercial, SIP, modular, and developer-led projects nationwide, supporting builders, consultants, and developers.
- Led business development, key client relationships, quoting, proposals, fee structures, and commercial negotiations.
- Developed internal SOPs, QA workflows, and production systems to standardise output and improve consistency across a distributed workforce.
- Built internal tools and software workflows, including automation, AI-assisted systems, and basic/full-stack development.

Skills: Leadership, Business Development, Architectural Delivery, Systems & Workflow Design, Remote Team Management, Negotiation, Creative Direction, Process Engineering, Automation & AI-Assisted Workflows

National Partner
Z500 | Oct 2017 - Present | Canterbury, New Zealand

Z500 is a global home design studio offering contemporary European-styled residential plans used by builders, investors, and developers worldwide. I introduced the brand into New Zealand, creating market awareness and establishing relationships across builder networks, investor groups, and architectural channels.

Key contributions:
- Brought the brand to NZ and launched distribution into local builder networks
- Positioned Z500 plans as cost-efficient, design-led alternatives for first homes through to high-end residential
- Promoted energy-efficient construction and modern modular-ready design principles
- Built sales funnels and marketing material including planbooks, digital campaigns, and builder partnerships

Business Development Director
Motovated Design & Analysis Ltd | Jan 2017 - Mar 2018 | Christchurch

I led business development across NZ and Australia, driving high-value mechanical design, simulation, and engineering analysis projects. My role sat at the intersection of sales, technical scoping, and delivery - opening doors with product & engineering leaders, shaping solutions with the technical team, and converting opportunities into profitable engagements.

Key Contributions:
- Led the sales function and team, shifting from reactive inbound to proactive pipeline generation
- Built relationships with OEMs, rail sector leaders, manufacturers, and product development teams across NZ + Australia
- Secured enterprise-level opportunities in mechanical design, FEA, prototyping, and failure analysis
- Developed sales strategy, campaigns, and targeted outreach into emerging markets (incl. rail)
- Represented the company at trade shows, engineering expos, and technical industry events
- Acted as the commercial-technical bridge, translating requirements into scoped work packages and signed contracts

BDM / Design Manager / New Home Sales
Holloway Builders | Jan 2016 - Jan 2017 | Christchurch

I was hired to drive new residential build opportunities across Christchurch and North Canterbury. The role quickly expanded to include design leadership, new home sales, showhome representation, and supporting the transition into the Platinum Homes franchise model.

Key Contributions:
- Led business development and sourced new residential + multi-unit opportunities
- Expanded role to include design leadership and architectural input
- Managed client engagement from first enquiry to signed contracts
- Hosted showhomes, trade events, and industry engagement campaigns
- Developed and launched a new modern website to support brand presence and sales funnels
- Supported transition into the Platinum Homes franchise model

Founding Director
DesignBASE Ltd | May 1998 - Apr 2016 | Invercargill, Central Otago and Nelson

I co-founded DesignBASE and helped grow it from a small start-up into a recognised multi-disciplinary architectural and engineering practice across Southland, Central Otago and Nelson.

Highlights:
- Grew the practice into a multi-office regional business combining architectural, structural, and mechanical design
- Drove the transition from manual workflows to advanced 3D modelling and CNC-ready fabrication
- Delivered work spanning residential, light commercial, marine, aviation, and industrial sectors

Notable Work:
- Stabicraft Marine - early mechanical design & CAD/CAM development
- AJ Hackett Bungy - structural steel shop drawings for Kawarau Bridge administration building
- Air New Zealand Engineering Services - Boeing 747 & 777 interior fit-out design support
- 'World's Fastest Indian' Burt Munro motorcycle exhibit display unit

Trade Business Manager - South Island (BGC Fibre Cement / INNOVA)
BGC Fibre Cement | Oct 2012 - Dec 2015 | South Island

Launched BGC Fibre Cement's INNOVA range into the South Island from virtually zero presence - building market share against James Hardie through direct engagement with specifiers, merchants, builders, and group home companies.

Key Wins:
- Established South Island market presence from the ground up
- Secured ranging across major merchant networks including Bunnings, PlaceMakers & ITM
- Specified product on 300+ multi-unit projects in Christchurch
- Won Top Salesperson Across BGC NZ + Australia (Perth Annual Conference)
- Built long-term relationships that continued to grow after handover

Earlier Career:
- Mechanical Engineering Technician, Henley Industries (1996-1998)
- Intermediate CAD Technician, Opus International Consultants (1994-1995)
- CAD Technician, Heaslip Engineering (1993-1994)
- Draughtsperson / Engineering Cadet, TH Jenkins & Associates (1987-1993)

Core Strengths:
- Sales & Business Development (construction, property, building products)
- New Home Sales & Real Estate
- Architectural Design & Technical Documentation
- Building Products & Merchant Channel Sales
- Remote Team Leadership & Offshore Delivery
- Systems Design, Automation & AI-Assisted Workflows
- High-Performance Building Envelopes, SIPs, Modular Construction
"""

def save_cv():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in .env")
        return

    client = create_client(url, key)

    # Check if CV exists
    existing = client.table("cv_profile").select("id").limit(1).execute()

    if existing.data:
        result = client.table("cv_profile").update(
            {"cv_text": CV_TEXT}
        ).eq("id", existing.data[0]["id"]).execute()
        print("CV updated!")
    else:
        result = client.table("cv_profile").insert(
            {"cv_text": CV_TEXT}
        ).execute()
        print("CV saved!")

    print(f"CV length: {len(CV_TEXT)} characters")

if __name__ == "__main__":
    save_cv()
