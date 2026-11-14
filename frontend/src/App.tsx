import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowDownUp,
  ArrowLeft,
  ArrowRight,
  Bell,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  ImagePlus,
  LogOut,
  MapPin,
  PackageCheck,
  Search,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react'
import {
  BrowserRouter,
  Link,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { NotificationProvider, useNotifications } from './context/NotificationContext'
import AdminDashboardPage from './pages/AdminDashboardPage'
import { categoriesApi, locationsApi } from './api/categories'
import { contactApi } from './api/contact'
import { getImageUrl } from './api/client'
import { itemsApi } from './api/items'
import type { FoundItemUpdatePayload } from './api/items'
import type {
  CampusLocation,
  Category,
  ContactRequest,
  FoundItemCard,
  FoundItemDetail,
  MyFoundItem,
  PaginatedItems,
} from './types'
import './App.css'

function localDateTimeValue(date = new Date()): string {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

function SiteHeader() {
  const { user, logout } = useAuth()
  const { unreadCount } = useNotifications()
  const navigate = useNavigate()

  const signOut = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="header-inner">
        <Link className="brand" to="/" aria-label="Found It home">
          <span className="brand-mark"><PackageCheck size={23} strokeWidth={2.2} /></span>
          <span>found<span className="brand-accent">it</span></span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          <Link to="/">Browse items</Link>
          {user && (
            <>
              <Link to="/my-listings">My listings</Link>
              <Link to="/my-enquiries">My enquiries</Link>
              {user.role === 'admin' && <Link to="/admin">Admin</Link>}
            </>
          )}
        </nav>
        <div className="header-actions">
          {user ? (
            <>
              <Link className="user-chip" to="/my-listings">
                <span className="avatar"><UserRound size={15} /></span>
                <span>{user.full_name.split(' ')[0]}</span>
              </Link>
              <Link className="notification-link" to="/my-enquiries" aria-label={`My enquiries${unreadCount ? `, ${unreadCount} unread notifications` : ''}`} title="My enquiries">
                <Bell size={18} />
                {unreadCount > 0 && <span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>}
              </Link>
              <button className="icon-button" type="button" onClick={signOut} aria-label="Sign out" title="Sign out">
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link className="signin-link" to="/auth">Sign in</Link>
              <Link className="button button-dark header-cta" to="/auth?mode=register">Create account</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <Link className="brand footer-brand" to="/">
          <span className="brand-mark"><PackageCheck size={20} /></span>
          <span>found<span className="brand-accent">it</span></span>
        </Link>
        <span>A little kindness goes a long way.</span>
        <span>Campus community, connected.</span>
      </div>
    </footer>
  )
}

function LoadingState({ label = 'Loading Found It...' }: { label?: string }) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-spinner" />
      <span>{label}</span>
    </div>
  )
}

function RequireAccount() {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <LoadingState label="Checking your account..." />
  if (!user) return <Navigate to="/auth" replace state={{ from: location }} />
  return <Outlet />
}

function RequireAdmin() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <LoadingState label="Checking administrator access..." />
  if (!user || user.role !== 'admin') return <Navigate to="/" replace />
  return <Outlet />
}

function ItemCard({ item }: { item: FoundItemCard | MyFoundItem }) {
  return (
    <Link className="item-card" to={`/items/${encodeURIComponent(item.reference_code)}`}>
      <div className="item-card-image">
        <img src={getImageUrl(item.primary_image)} alt={item.title} loading="lazy" />
        <span className="item-category">{item.category.name}</span>
      </div>
      <div className="item-card-content">
        <div className="item-card-meta">
          <span><MapPin size={14} />{item.location.building_or_area}</span>
          <span><Clock3 size={14} />{new Date(item.found_at).toLocaleDateString()}</span>
        </div>
        <h3>{item.title}</h3>
        <p>{item.description}</p>
        <div className="item-card-footer">
          <span className={`status-pill status-${item.status}`}>{item.status}</span>
          <span className="reference-code">{item.reference_code}</span>
        </div>
      </div>
    </Link>
  )
}

function HomePage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [query, setQuery] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [locationId, setLocationId] = useState('')
  const [sort, setSort] = useState('newest')
  const [filters, setFilters] = useState<{
    q?: string
    category_id?: number
    location_id?: number
    sort: string
    page: number
    page_size: number
  } | null>(null)
  const [results, setResults] = useState<PaginatedItems | null>(null)
  const [loadingReferences, setLoadingReferences] = useState(true)
  const [loadingResults, setLoadingResults] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([categoriesApi.getAll(), locationsApi.getAll()])
      .then(([categoryData, locationData]) => {
        if (!active) return
        setCategories(categoryData)
        setLocations(locationData)
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoadingReferences(false)
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!filters) return
    let active = true
    itemsApi.search(filters)
      .then((data) => {
        if (active) setResults(data)
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoadingResults(false)
      })
    return () => { active = false }
  }, [filters])

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoadingResults(true)
    setError('')
    setFilters({
      q: query.trim() || undefined,
      category_id: categoryId ? Number(categoryId) : undefined,
      location_id: locationId ? Number(locationId) : undefined,
      sort,
      page: 1,
      page_size: 12,
    })
  }

  const browseAll = () => {
    setLoadingResults(true)
    setError('')
    setQuery('')
    setCategoryId('')
    setLocationId('')
    setFilters({ sort, page: 1, page_size: 12 })
  }

  const changePage = (page: number) => {
    setLoadingResults(true)
    setError('')
    setFilters((current) => current ? { ...current, page } : current)
  }

  return (
    <>
      <section className="hero-section">
        <div className="hero-glow hero-glow-one" />
        <div className="hero-glow hero-glow-two" />
        <div className="hero-content">
          <div className="eyebrow"><Sparkles size={14} /> A kinder campus starts here</div>
          <h1>Found something?<br /><span>Help it find its way home.</span></h1>
          <p className="hero-copy">
            Browse items found around campus, or share what you found so its owner can find it.
          </p>
          <form className="search-panel" onSubmit={submitSearch}>
            <label className="search-input-wrap">
              <Search size={19} />
              <input
                type="search"
                placeholder="Try a blue water bottle or a reference code"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <label className="select-wrap">
              <span className="sr-only">Category</span>
              <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)} disabled={loadingReferences}>
                <option value="">All categories</option>
                {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
              </select>
            </label>
            <label className="select-wrap">
              <span className="sr-only">Campus location</span>
              <select value={locationId} onChange={(event) => setLocationId(event.target.value)} disabled={loadingReferences}>
                <option value="">All locations</option>
                {locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
              </select>
            </label>
            <button className="button button-orange search-submit" type="submit">
              Search <ArrowRight size={17} />
            </button>
          </form>
          <button className="text-button browse-link" type="button" onClick={browseAll}>
            Browse all found items <ArrowRight size={15} />
          </button>
          <div className="hero-note">
            <ShieldCheck size={16} /> Only found-item reports. Your contact details stay private.
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-art-orbit orbit-one" />
          <div className="hero-art-orbit orbit-two" />
          <div className="hero-art-card">
            <div className="hero-art-photo"><PackageCheck size={76} strokeWidth={1.2} /></div>
            <div className="hero-art-label"><span className="hero-art-dot" /><span><b>Found nearby</b><small>Ready to find its owner</small></span></div>
          </div>
          <div className="floating-note"><CheckCircle2 size={17} /> Good things get returned</div>
        </div>
      </section>

      <main className="page-content">
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {filters ? (
          <section className="results-section" aria-live="polite">
            <div className="section-heading results-heading">
              <div>
                <span className="section-kicker">Campus finds</span>
                <h2>{loadingResults ? 'Looking around...' : `${results?.total ?? 0} found ${results?.total === 1 ? 'item' : 'items'}`}</h2>
                <p>Every listing is a found item, reported by someone on campus.</p>
              </div>
              <label className="sort-control">
                <ArrowDownUp size={16} />
                <span className="sr-only">Sort results</span>
                <select
                  value={sort}
                  onChange={(event) => {
                    setLoadingResults(true)
                    setError('')
                    setSort(event.target.value)
                    setFilters((current) => current ? { ...current, sort: event.target.value, page: 1 } : current)
                  }}
                >
                  <option value="newest">Newest first</option>
                  <option value="oldest">Oldest first</option>
                  <option value="category">Category</option>
                  <option value="location">Location</option>
                </select>
              </label>
            </div>
            {loadingResults ? (
              <LoadingState label="Searching found-item reports..." />
            ) : results?.items.length ? (
              <>
                <div className="item-grid">
                  {results.items.map((item) => <ItemCard item={item} key={item.id} />)}
                </div>
                {results.total_pages > 1 && (
                  <div className="pagination">
                    <button className="button button-outline" type="button" disabled={results.page <= 1} onClick={() => changePage(results.page - 1)}>
                      <ChevronLeft size={17} /> Previous
                    </button>
                    <span>Page {results.page} of {results.total_pages}</span>
                    <button className="button button-outline" type="button" disabled={results.page >= results.total_pages} onClick={() => changePage(results.page + 1)}>
                      Next <ChevronRight size={17} />
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">
                <div className="empty-icon"><Search size={25} /></div>
                <h3>No found items match those filters</h3>
                <p>Try a different keyword, category, or campus location.</p>
                <button className="button button-dark" type="button" onClick={browseAll}>Browse all reports</button>
              </div>
            )}
          </section>
        ) : (
          <section className="welcome-strip">
            <div className="welcome-icon"><CircleHelp size={22} /></div>
            <div><h2>Looking for something?</h2><p>Search found reports above, or browse every available item to see what's been turned in.</p></div>
            <button className="button button-outline" type="button" onClick={browseAll}>Browse reports <ArrowRight size={16} /></button>
          </section>
        )}

        <section className="how-section">
          <div className="section-heading">
            <div><span className="section-kicker">How Found It works</span><h2>Small steps, happier endings.</h2></div>
          </div>
          <div className="how-grid">
            <article className="how-card"><span className="how-number">01</span><div className="how-icon"><Search size={21} /></div><h3>Search found reports</h3><p>Filter by category or campus location to narrow down the items people have found.</p></article>
            <article className="how-card"><span className="how-number">02</span><div className="how-icon"><ImagePlus size={21} /></div><h3>Share what you found</h3><p>Post a photo and a few details so the right person can recognize their belonging.</p></article>
            <article className="how-card"><span className="how-number">03</span><div className="how-icon"><PackageCheck size={21} /></div><h3>Help it get home</h3><p>Use the item's reference code when coordinating a safe return through campus.</p></article>
          </div>
        </section>
      </main>
    </>
  )
}

function ItemDetailPage() {
  const { referenceCode = '' } = useParams()
  const { user } = useAuth()
  const location = useLocation()
  const [item, setItem] = useState<FoundItemDetail | null>(null)
  const [loadedReference, setLoadedReference] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [contactError, setContactError] = useState('')
  const [contactSent, setContactSent] = useState(false)
  const [sending, setSending] = useState(false)
  const loading = loadedReference !== referenceCode

  useEffect(() => {
    let active = true
    itemsApi.getByReference(referenceCode)
      .then((data) => {
        if (active) {
          setItem(data)
          setError('')
          setLoadedReference(referenceCode)
        }
      })
      .catch((requestError: Error) => {
        if (active) {
          setItem(null)
          setError(requestError.message)
          setLoadedReference(referenceCode)
        }
      })
    return () => { active = false }
  }, [referenceCode])

  const sendEnquiry = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!item) return
    setSending(true)
    setContactError('')
    setContactSent(false)
    try {
      await contactApi.sendContactRequest(item.id, message.trim())
      setMessage('')
      setContactSent(true)
    } catch (requestError) {
      setContactError(requestError instanceof Error ? requestError.message : 'Unable to send your enquiry.')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <main className="page-content"><LoadingState label="Opening item details..." /></main>
  if (!item) {
    return (
      <main className="page-content">
        <div className="detail-error">
          <CircleHelp size={28} />
          <h1>We couldn't find that item</h1>
          <p>{error || 'This found-item report may no longer be publicly available.'}</p>
          <Link className="button button-dark" to="/">Back to search</Link>
        </div>
      </main>
    )
  }

  const primaryImage = item.images.find((image) => image.is_primary) ?? item.images[0]
  return (
    <main className="page-content detail-page">
      <Link to="/" className="back-link"><ArrowLeft size={16} /> Back to search</Link>
      <div className="detail-layout">
        <div className="detail-image">
          <img src={getImageUrl(primaryImage?.image_path)} alt={item.title} />
          <span className={`status-pill status-${item.status}`}>{item.status}</span>
        </div>
        <article className="detail-info">
          <div className="detail-eyebrow">{item.category.name}{item.subcategory ? ` | ${item.subcategory.name}` : ''}</div>
          <h1>{item.title}</h1>
          <div className="detail-reference">Reference <strong>{item.reference_code}</strong></div>
          <p className="detail-description">{item.description}</p>
          <div className="detail-facts">
            <div><MapPin size={18} /><span><small>Found at</small><strong>{item.location.name}</strong><small>{item.location.building_or_area}</small></span></div>
            <div><Clock3 size={18} /><span><small>Date found</small><strong>{new Date(item.found_at).toLocaleString()}</strong></span></div>
            <div><UserRound size={18} /><span><small>Reported by</small><strong>{item.reporter.full_name}</strong>{item.reporter.department && <small>{item.reporter.department}</small>}</span></div>
          </div>
          <div className="detail-help">
            <ShieldCheck size={20} />
            <p>Keep this reference code handy when asking about this item. Personal contact information is never shown publicly.</p>
          </div>
          {item.is_owner ? (
            <div className="contact-panel contact-owner">
              <PackageCheck size={19} />
              <div><strong>This is your found-item report.</strong><Link to="/my-listings">Manage your listing</Link></div>
            </div>
          ) : item.status === 'available' && user ? (
            <form className="contact-panel contact-form" onSubmit={sendEnquiry}>
              <div><span className="section-kicker">Think this could be yours?</span><h2>Contact the reporter</h2></div>
              <p>Share enough detail for them to help verify the item. Your email and phone stay private.</p>
              {contactError && <div className="alert alert-error" role="alert">{contactError}</div>}
              {contactSent && <div className="alert alert-success" role="status">Your enquiry was sent. The reporter has been notified.</div>}
              <label className="field-label">Your message
                <textarea value={message} onChange={(event) => setMessage(event.target.value)} required minLength={10} maxLength={2000} rows={4} placeholder="Describe a detail that helps identify this item..." />
              </label>
              <button className="button button-orange" type="submit" disabled={sending}>
                {sending ? 'Sending...' : 'Send enquiry'} <ArrowRight size={17} />
              </button>
            </form>
          ) : item.status === 'available' ? (
            <div className="contact-panel contact-gate">
              <div><h2>Recognize this item?</h2><p>Sign in to send a private enquiry to the person who found it.</p></div>
              <Link className="button button-dark" to="/auth" state={{ from: location }}>Sign in to contact</Link>
            </div>
          ) : (
            <div className="contact-panel contact-owner">
              <PackageCheck size={19} />
              <div><strong>This item is no longer available for contact.</strong><span>Its report remains in your listing history.</span></div>
            </div>
          )}
        </article>
      </div>
    </main>
  )
}

function AuthPage() {
  const { login, register, user } = useAuth()
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>(searchParams.get('mode') === 'register' ? 'register' : 'login')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const routeState = location.state as { from?: { pathname?: string; search?: string } } | null
  const destination = `${routeState?.from?.pathname ?? '/'}${routeState?.from?.search ?? ''}`

  if (user) return <Navigate to={destination} replace />

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      if (mode === 'register') {
        await register({
          full_name: String(formData.get('full_name') ?? ''),
          email: String(formData.get('email') ?? ''),
          password: String(formData.get('password') ?? ''),
          department: String(formData.get('department') ?? '') || undefined,
          phone: String(formData.get('phone') ?? '') || undefined,
        })
      } else {
        await login(
          String(formData.get('email') ?? ''),
          String(formData.get('password') ?? ''),
        )
      }
      navigate(destination, { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to authenticate. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-icon"><PackageCheck size={26} /></div>
        <span className="section-kicker">{mode === 'register' ? 'Join your campus community' : 'Welcome back'}</span>
        <h1>{mode === 'register' ? 'Create your account' : 'Sign in to Found It'}</h1>
        <p className="auth-intro">{mode === 'register' ? 'Report found items and help them get back to their owners.' : 'Sign in to manage your found-item reports.'}</p>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <form className="form-stack" onSubmit={submit}>
          {mode === 'register' && (
            <>
              <label className="field-label">Full name<input name="full_name" type="text" autoComplete="name" required minLength={2} maxLength={150} /></label>
              <div className="form-row">
                <label className="field-label">Department <span>optional</span><input name="department" type="text" autoComplete="organization-title" maxLength={100} /></label>
                <label className="field-label">Phone <span>optional</span><input name="phone" type="tel" autoComplete="tel" maxLength={50} /></label>
              </div>
            </>
          )}
          <label className="field-label">Campus email<input name="email" type="email" autoComplete="email" required /></label>
          <label className="field-label">Password<input name="password" type="password" autoComplete={mode === 'register' ? 'new-password' : 'current-password'} required minLength={6} /></label>
          <button className="button button-orange button-wide" type="submit" disabled={busy}>
            {busy ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Sign in'} <ArrowRight size={17} />
          </button>
        </form>
        <p className="auth-switch">
          {mode === 'register' ? 'Already have an account?' : 'New to Found It?'}{' '}
          <button type="button" onClick={() => { setError(''); setMode(mode === 'register' ? 'login' : 'register') }}>
            {mode === 'register' ? 'Sign in' : 'Create an account'}
          </button>
        </p>
        <p className="privacy-note"><ShieldCheck size={15} /> Your account details are kept private.</p>
      </div>
    </main>
  )
}

interface ReportForm {
  title: string
  description: string
  categoryId: string
  subcategoryId: string
  locationId: string
  foundAt: string
  quantity: string
  condition: string
}

function ReportPage() {
  const [searchParams] = useSearchParams()
  const editParam = searchParams.get('edit')
  const editId = editParam && Number.isInteger(Number(editParam)) ? Number(editParam) : undefined
  const navigate = useNavigate()
  const [categories, setCategories] = useState<Category[]>([])
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [itemToEdit, setItemToEdit] = useState<MyFoundItem | null>(null)
  const [form, setForm] = useState<ReportForm>({
    title: '',
    description: '',
    categoryId: '',
    subcategoryId: '',
    locationId: '',
    foundAt: localDateTimeValue(),
    quantity: '1',
    condition: '',
  })
  const [image, setImage] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function loadFormData() {
      try {
        const [categoryData, locationData] = await Promise.all([
          categoriesApi.getAll(),
          locationsApi.getAll(),
        ])
        if (!active) return
        setCategories(categoryData)
        setLocations(locationData)
        if (editId) {
          const myItems = await itemsApi.getMyItems()
          const selected = myItems.find((item) => item.id === editId)
          if (!selected) throw new Error('You can only edit one of your own found-item reports.')
          if (!active) return
          setItemToEdit(selected)
          setForm({
            title: selected.title,
            description: selected.description,
            categoryId: String(selected.category.id),
            subcategoryId: selected.subcategory ? String(selected.subcategory.id) : '',
            locationId: String(selected.location.id),
            foundAt: localDateTimeValue(new Date(selected.found_at)),
            quantity: String(selected.quantity),
            condition: selected.condition ?? '',
          })
        }
      } catch (requestError) {
        if (active) setError(requestError instanceof Error ? requestError.message : 'Unable to load the report form.')
      } finally {
        if (active) setLoading(false)
      }
    }
    loadFormData()
    return () => { active = false }
  }, [editId])

  const selectedCategory = categories.find((category) => String(category.id) === form.categoryId)
  const updateForm = (key: keyof ReportForm, value: string) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const submitReport = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    if (!editId && !image) {
      setError('Add at least one photo so the owner can recognize the item.')
      return
    }
    if (image && image.size > 5 * 1024 * 1024) {
      setError('The photo must be 5 MB or smaller.')
      return
    }

    setBusy(true)
    try {
      const foundAt = new Date(form.foundAt).toISOString()
      if (editId) {
        const update: FoundItemUpdatePayload = {
          title: form.title.trim(),
          description: form.description.trim(),
          category_id: Number(form.categoryId),
          location_id: Number(form.locationId),
          found_at: foundAt,
          quantity: Number(form.quantity),
          condition: form.condition.trim() || undefined,
          subcategory_id: form.subcategoryId ? Number(form.subcategoryId) : null,
        }
        const updated = await itemsApi.update(editId, update)
        navigate(`/items/${encodeURIComponent(updated.reference_code)}`)
      } else {
        if (!image) throw new Error('Add a photo before publishing this report.')
        const body = new FormData()
        body.append('title', form.title.trim())
        body.append('description', form.description.trim())
        body.append('category_id', form.categoryId)
        body.append('location_id', form.locationId)
        body.append('found_at', foundAt)
        body.append('quantity', form.quantity)
        if (form.subcategoryId) body.append('subcategory_id', form.subcategoryId)
        if (form.condition.trim()) body.append('condition', form.condition.trim())
        body.append('image', image)
        const created = await itemsApi.create(body)
        navigate(`/items/${encodeURIComponent(created.reference_code)}`)
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to save this report.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <main className="page-content"><LoadingState label="Preparing your report form..." /></main>

  return (
    <main className="page-content form-page">
      <Link to="/my-listings" className="back-link"><ArrowLeft size={16} /> Back to my listings</Link>
      <div className="form-page-heading">
        <span className="section-kicker">{editId ? 'Keep your report up to date' : 'Be someone’s good news'}</span>
        <h1>{editId ? 'Edit found-item report' : 'Report a found item'}</h1>
        <p>{editId ? 'Update the details so the owner can recognize it.' : 'Share a few details and a clear photo to help this item find its owner.'}</p>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <form className="report-form" onSubmit={submitReport}>
        <div className="report-form-main">
          <label className="field-label">Item name<input value={form.title} onChange={(event) => updateForm('title', event.target.value)} required minLength={3} maxLength={200} placeholder="e.g. Blue insulated water bottle" /></label>
          <label className="field-label">Description<textarea value={form.description} onChange={(event) => updateForm('description', event.target.value)} required minLength={10} rows={5} placeholder="Add helpful details such as colour, brand, or where you found it..." /></label>
          <div className="form-row">
            <label className="field-label">Category
              <select value={form.categoryId} onChange={(event) => { updateForm('categoryId', event.target.value); updateForm('subcategoryId', '') }} required>
                <option value="">Choose a category</option>
                {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
              </select>
            </label>
            <label className="field-label">Item type <span>optional</span>
              <select value={form.subcategoryId} onChange={(event) => updateForm('subcategoryId', event.target.value)} disabled={!selectedCategory?.subcategories.length}>
                <option value="">Choose a type</option>
                {selectedCategory?.subcategories.map((subcategory) => <option key={subcategory.id} value={subcategory.id}>{subcategory.name}</option>)}
              </select>
            </label>
          </div>
          <label className="field-label">Campus location
            <select value={form.locationId} onChange={(event) => updateForm('locationId', event.target.value)} required>
              <option value="">Where did you find it?</option>
              {locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
            </select>
          </label>
          <div className="form-row">
            <label className="field-label">Date and time found<input type="datetime-local" value={form.foundAt} onChange={(event) => updateForm('foundAt', event.target.value)} required /></label>
            <label className="field-label">Quantity<input type="number" min="1" max="99" value={form.quantity} onChange={(event) => updateForm('quantity', event.target.value)} required /></label>
          </div>
          <label className="field-label">Condition <span>optional</span><input value={form.condition} onChange={(event) => updateForm('condition', event.target.value)} maxLength={50} placeholder="e.g. Good" /></label>
        </div>
        <aside className="report-form-aside">
          <div className="upload-panel">
            <div className="upload-icon"><ImagePlus size={24} /></div>
            <h2>{editId ? 'Item photo' : 'Add a photo'}</h2>
            <p>A clear photo helps the owner confirm their belonging. Avoid showing private information.</p>
            {itemToEdit?.primary_image && !image && <img className="upload-preview" src={getImageUrl(itemToEdit.primary_image)} alt="Current item" />}
            {!editId && (
              <>
                <label className="button button-outline upload-button">
                  <ImagePlus size={17} /> {image ? 'Choose a different photo' : 'Choose photo'}
                  <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setImage(event.target.files?.[0] ?? null)} required />
                </label>
                <span className="upload-help">{image ? image.name : 'JPG, PNG or WebP - up to 5 MB'}</span>
                <span className="required-photo">A photo is required for a new report.</span>
              </>
            )}
            {editId && <span className="required-photo">The original photo stays attached when you edit a report.</span>}
          </div>
          <div className="privacy-card"><ShieldCheck size={18} /><p>Your email and phone are never displayed on public listings.</p></div>
          <button className="button button-orange button-wide" type="submit" disabled={busy}>
            {busy ? 'Saving report...' : editId ? 'Save changes' : 'Publish found item'} <ArrowRight size={17} />
          </button>
        </aside>
      </form>
    </main>
  )
}

function MyListingsPage() {
  const [items, setItems] = useState<MyFoundItem[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    itemsApi.getMyItems()
      .then((data) => {
        if (active) setItems(data)
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const changeStatus = async (item: MyFoundItem, nextStatus: 'available' | 'returned' | 'removed') => {
    setBusyId(item.id)
    setError('')
    try {
      await itemsApi.updateStatus(item.id, nextStatus)
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, status: nextStatus } : entry))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to update this listing.')
    } finally {
      setBusyId(null)
    }
  }

  const archiveItem = async (item: MyFoundItem) => {
    if (!window.confirm('Archive this listing? It will stay in your records but disappear from public search.')) return
    setBusyId(item.id)
    setError('')
    try {
      await itemsApi.delete(item.id)
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, status: 'removed' } : entry))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to archive this listing.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <main className="page-content listings-page">
      <div className="listings-heading">
        <div><span className="section-kicker">Your reports</span><h1>My listings</h1><p>Manage the found items you’ve shared with campus.</p></div>
        <Link className="button button-orange" to="/report"><ImagePlus size={17} /> Report an item</Link>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {loading ? <LoadingState label="Loading your listings..." /> : items.length ? (
        <div className="my-listings">
          {items.map((item) => (
            <article className="my-listing" key={item.id}>
              <Link className="my-listing-image" to={`/items/${encodeURIComponent(item.reference_code)}`}>
                <img src={getImageUrl(item.primary_image)} alt={item.title} loading="lazy" />
              </Link>
              <div className="my-listing-info">
                <div className="my-listing-topline"><span className={`status-pill status-${item.status}`}>{item.status}</span><span className="reference-code">{item.reference_code}</span></div>
                <Link to={`/items/${encodeURIComponent(item.reference_code)}`} className="my-listing-title">{item.title}</Link>
                <p>{item.location.name} | Found {new Date(item.found_at).toLocaleDateString()}</p>
                <p className="my-listing-description">{item.description}</p>
                <div className="listing-actions">
                  <Link className="button button-outline button-small" to={`/report?edit=${item.id}`}>Edit report</Link>
                  {item.status !== 'returned' && <button className="button button-outline button-small" type="button" disabled={busyId === item.id} onClick={() => changeStatus(item, 'returned')}>{busyId === item.id ? 'Saving...' : 'Mark returned'}</button>}
                  {item.status !== 'available' && <button className="text-button" type="button" disabled={busyId === item.id} onClick={() => changeStatus(item, 'available')}>Reopen listing</button>}
                  {item.status !== 'removed' && <button className="text-button text-danger" type="button" disabled={busyId === item.id} onClick={() => archiveItem(item)}>Archive</button>}
                </div>
              </div>
              <div className="listing-enquiries"><span>{item.contact_count}</span><small>enquiries</small></div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state listings-empty">
          <div className="empty-icon"><PackageCheck size={25} /></div>
          <h2>No found-item reports yet</h2>
          <p>When you find something on campus, post it here to help its owner find it.</p>
          <Link className="button button-orange" to="/report"><ImagePlus size={17} /> Report a found item</Link>
        </div>
      )}
    </main>
  )
}

function EnquiryCard({
  request,
  direction,
  busy,
  onStatusChange,
}: {
  request: ContactRequest
  direction: 'sent' | 'received'
  busy: boolean
  onStatusChange: (request: ContactRequest, status: 'new' | 'read' | 'closed') => void
}) {
  const otherPerson = direction === 'received' ? request.sender : request.recipient
  const canOpenItem = request.item.status === 'available' || direction === 'received'

  return (
    <article className="enquiry-card">
      <div className="enquiry-card-top">
        <span className={`status-pill enquiry-${request.status}`}>{request.status}</span>
        <time>{new Date(request.created_at).toLocaleString()}</time>
      </div>
      <h3>{direction === 'received' ? `Enquiry from ${otherPerson.full_name}` : `Enquiry to ${otherPerson.full_name}`}</h3>
      <p className="enquiry-item">
        {canOpenItem
          ? <Link to={`/items/${encodeURIComponent(request.item.reference_code)}`}>{request.item.title} <span>({request.item.reference_code})</span></Link>
          : <>{request.item.title} <span>({request.item.reference_code})</span></>}
      </p>
      <blockquote>{request.message}</blockquote>
      {direction === 'received' && (
        <div className="enquiry-actions">
          {request.status === 'new' && <button className="button button-outline button-small" type="button" disabled={busy} onClick={() => onStatusChange(request, 'read')}>Mark as read</button>}
          {request.status !== 'closed' && <button className="button button-outline button-small" type="button" disabled={busy} onClick={() => onStatusChange(request, 'closed')}>Close enquiry</button>}
          {request.status === 'closed' && <button className="text-button" type="button" disabled={busy} onClick={() => onStatusChange(request, 'new')}>Reopen</button>}
          {busy && <span className="enquiry-saving">Saving...</span>}
        </div>
      )}
    </article>
  )
}

function MyEnquiriesPage() {
  const [sent, setSent] = useState<ContactRequest[]>([])
  const [received, setReceived] = useState<ContactRequest[]>([])
  const [tab, setTab] = useState<'received' | 'sent'>('received')
  const [loading, setLoading] = useState(true)
  const [busyRequestId, setBusyRequestId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const { notifications: liveNotifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()
  const activeRequests = tab === 'received' ? received : sent

  useEffect(() => {
    let active = true
    Promise.all([
      contactApi.getSentRequests(),
      contactApi.getReceivedRequests(),
    ])
      .then(([sentRequests, receivedRequests]) => {
        if (!active) return
        setSent(sentRequests)
        setReceived(receivedRequests)
      })
      .catch((requestError: Error) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const updateRequestStatus = async (request: ContactRequest, nextStatus: 'new' | 'read' | 'closed') => {
    setBusyRequestId(request.id)
    setError('')
    try {
      const updated = await contactApi.updateRequestStatus(request.id, nextStatus)
      setReceived((current) => current.map((entry) => entry.id === updated.id ? updated : entry))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to update this enquiry.')
    } finally {
      setBusyRequestId(null)
    }
  }

  const markAllNotifications = async () => {
    try {
      await markAllAsRead()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to update notifications.')
    }
  }

  const shownNotifications = liveNotifications.filter((notification) => !notification.is_read).slice(0, 5)

  return (
    <main className="page-content enquiries-page">
      <div className="listings-heading">
        <div><span className="section-kicker">Private messages</span><h1>My enquiries</h1><p>Keep track of found-item enquiries you have sent and received.</p></div>
        <Link className="button button-outline" to="/">Browse items <ArrowRight size={16} /></Link>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <section className="notifications-panel">
        <div className="notifications-heading">
          <div><span className="section-kicker">Updates</span><h2>Notifications {unreadCount > 0 && <span>{unreadCount} new</span>}</h2></div>
          {unreadCount > 0 && <button className="text-button" type="button" onClick={markAllNotifications}>Mark all read</button>}
        </div>
        {shownNotifications.length ? (
          <div className="notifications-list">
            {shownNotifications.map((notification) => (
              <article className="notification-row" key={notification.id}>
                <span className="notification-dot" />
                <div><strong>{notification.title}</strong><p>{notification.message}</p><time>{new Date(notification.created_at).toLocaleString()}</time></div>
                <button className="text-button" type="button" onClick={() => {
                  void markAsRead(notification.id).catch((requestError: Error) => setError(requestError.message))
                }}>Mark read</button>
              </article>
            ))}
          </div>
        ) : <p className="notification-empty">You are all caught up.</p>}
      </section>
      <div className="enquiry-tabs" role="tablist" aria-label="Enquiry type">
        <button type="button" role="tab" aria-selected={tab === 'received'} className={tab === 'received' ? 'active' : ''} onClick={() => setTab('received')}>Received <span>{received.length}</span></button>
        <button type="button" role="tab" aria-selected={tab === 'sent'} className={tab === 'sent' ? 'active' : ''} onClick={() => setTab('sent')}>Sent <span>{sent.length}</span></button>
      </div>
      {loading ? <LoadingState label="Loading your enquiries..." /> : activeRequests.length ? (
        <div className="enquiry-list">
          {activeRequests.map((request) => (
            <EnquiryCard
              key={request.id}
              request={request}
              direction={tab}
              busy={busyRequestId === request.id}
              onStatusChange={updateRequestStatus}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state enquiries-empty">
          <div className="empty-icon"><Bell size={24} /></div>
          <h2>No {tab} enquiries</h2>
          <p>{tab === 'received' ? 'When someone contacts you about a found item, it will appear here.' : 'Enquiries you send about found items will appear here.'}</p>
          {tab === 'sent' && <Link className="button button-orange" to="/">Search found items</Link>}
        </div>
      )}
    </main>
  )
}

function AppRoutes() {
  return (
    <div className="app-shell">
      <SiteHeader />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/items/:referenceCode" element={<ItemDetailPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route element={<RequireAccount />}>
          <Route path="/report" element={<ReportPage />} />
          <Route path="/my-listings" element={<MyListingsPage />} />
          <Route path="/my-enquiries" element={<MyEnquiriesPage />} />
          <Route element={<RequireAdmin />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <SiteFooter />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <AppRoutes />
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
