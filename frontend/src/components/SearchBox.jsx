import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Clock, 
  Database, 
  File, 
  Search, 
  Server, 
  Settings, 
  Shield, 
  Users, 
  X 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { searchSystem } from '@/api/search';

const SearchBox = () => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({
    queries: [],
    servers: [],
    users: [],
    docs: [],
    pages: []
  });
  const [isSearching, setIsSearching] = useState(false);
  const [recentSearches, setRecentSearches] = useState(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('recentSearches');
    return saved ? JSON.parse(saved) : [];
  });
  
  const navigate = useNavigate();
  const searchTimeoutRef = useRef(null);
  
  // Keyboard shortcut to open search
  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);
  
  // Save recent searches to localStorage
  useEffect(() => {
    localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
  }, [recentSearches]);
  
  // Handle search when query changes
  useEffect(() => {
    if (!query.trim()) {
      setResults({
        queries: [],
        servers: [],
        users: [],
        docs: [],
        pages: []
      });
      setIsSearching(false);
      return;
    }
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    setIsSearching(true);
    
    // Debounce search to avoid too many requests
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const searchResults = await searchSystem(query);
        setResults(searchResults);
      } catch (error) {
        console.error('Error searching:', error);
        // Mock data for demonstration
        setResults({
          queries: [
            { id: 1, text: 'SELECT * FROM customers WHERE country = "Turkey"', type: 'whitelist' },
            { id: 2, text: 'SELECT product_id, COUNT(*) FROM orders GROUP BY product_id', type: 'history' }
          ],
          servers: [
            { id: 'prod_finance', name: 'Finance Production' },
            { id: 'reporting_dw', name: 'Reporting Data Warehouse' }
          ],
          users: [
            { id: 'teeksss', name: 'Teeksss', role: 'admin' },
            { id: 'analyst1', name: 'Data Analyst', role: 'analyst' }
          ],
          docs: [
            { id: 'sql-basics', title: 'SQL Temel Komutlar', category: 'Dokümantasyon' },
            { id: 'whitelist-guide', title: 'Beyaz Liste Yönetimi', category: 'Rehber' }
          ],
          pages: [
            { id: 'dashboard', title: 'Dashboard', path: '/dashboard' },
            { id: 'query_approval', title: 'Sorgu Onayları', path: '/admin/query-approval' },
            { id: 'whitelist', title: 'Beyaz Liste', path: '/admin/whitelist' },
            { id: 'audit_logs', title: 'Audit Loglar', path: '/admin/audit-logs' }
          ]
        });
      } finally {
        setIsSearching(false);
      }
    }, 300);
    
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query]);
  
  const handleSelect = (item, type) => {
    // Add to recent searches
    const newSearch = { text: query, timestamp: new Date().toISOString() };
    setRecentSearches(prev => {
      const filtered = prev.filter(item => item.text !== query);
      return [newSearch, ...filtered].slice(0, 5); // Keep last 5 searches
    });
    
    // Navigate or perform action based on selected item type
    switch (type) {
      case 'page':
        navigate(item.path);
        break;
      case 'query':
        if (item.type === 'whitelist') {
          navigate(`/admin/whitelist?query=${encodeURIComponent(item.text)}`);
        } else {
          navigate(`/dashboard?query=${encodeURIComponent(item.text)}`);
        }
        break;
      case 'server':
        navigate(`/admin/servers?server=${item.id}`);
        break;
      case 'user':
        navigate(`/admin/roles?user=${item.id}`);
        break;
      case 'doc':
        navigate(`/help?doc=${item.id}`);
        break;
      default:
        break;
    }
    
    setOpen(false);
  };
  
  const clearRecentSearches = () => {
    setRecentSearches([]);
  };
  
  return (
    <>
      <Button
        variant="outline"
        className="relative h-9 w-9 p-0 xl:h-10 xl:w-60 xl:justify-start xl:px-3 xl:py-2"
        onClick={() => setOpen(true)}
      >
        <Search className="h-4 w-4 xl:mr-2" />
        <span className="hidden xl:inline-flex">Ara...</span>
        <span className="sr-only">Ara</span>
        <kbd className="pointer-events-none absolute right-1.5 top-2 hidden h-6 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-xs font-medium opacity-100 xl:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>
      
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="Ara..."
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          {isSearching ? (
            <div className="flex justify-center items-center py-6">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-800"></div>
            </div>
          ) : query.length === 0 ? (
            <>
              <CommandGroup heading="Son Aramalar">
                {recentSearches.length > 0 ? (
                  <>
                    {recentSearches.map((item, index) => (
                      <CommandItem
                        key={index}
                        onSelect={() => {
                          setQuery(item.text);
                        }}
                      >
                        <Clock className="mr-2 h-4 w-4" />
                        <span>{item.text}</span>
                      </CommandItem>
                    ))}
                    <CommandItem onSelect={clearRecentSearches}>
                      <X className="mr-2 h-4 w-4" />
                      <span className="text-sm text-muted-foreground">Son aramaları temizle</span>
                    </CommandItem>
                  </>
                ) : (
                  <CommandEmpty>Son arama geçmişi bulunamadı.</CommandEmpty>
                )}
              </CommandGroup>
              
              <CommandSeparator />
              
              <CommandGroup heading="Hızlı Erişim">
                <CommandItem onSelect={() => navigate('/dashboard')}>
                  <Database className="mr-2 h-4 w-4" />
                  <span>Sorgu Paneli</span>
                </CommandItem>
                <CommandItem onSelect={() => navigate('/admin/query-approval')}>
                  <Shield className="mr-2 h-4 w-4" />
                  <span>Sorgu Onayları</span>
                </CommandItem>
                <CommandItem onSelect={() => navigate('/admin/audit-logs')}>
                  <Clock className="mr-2 h-4 w-4" />
                  <span>Audit Loglar</span>
                </CommandItem>
                <CommandItem onSelect={() => navigate('/admin/servers')}>
                  <Server className="mr-2 h-4 w-4" />
                  <span>Sunucular</span>
                </CommandItem>
                <CommandItem onSelect={() => navigate('/admin/roles')}>
                  <Users className="mr-2 h-4 w-4" />
                  <span>Kullanıcı Rolleri</span>
                </CommandItem>
                <CommandItem onSelect={() => navigate('/settings')}>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Ayarlar</span>
                </CommandItem>
              </CommandGroup>
            </>
          ) : (
            <>
              {/* Queries */}
              {results.queries.length > 0 && (
                <CommandGroup heading="Sorgular">
                  {results.queries.map((item) => (
                    <CommandItem 
                      key={`query-${item.id}`}
                      onSelect={() => handleSelect(item, 'query')}
                    >
                      <Database className="mr-2 h-4 w-4" />
                      <div className="overflow-hidden text-ellipsis">
                        <span className="line-clamp-1">{item.text}</span>
                        <span className="text-xs text-muted-foreground">
                          {item.type === 'whitelist' ? 'Beyaz Liste' : 'Geçmiş'}
                        </span>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              
              {/* Pages */}
              {results.pages.length > 0 && (
                <CommandGroup heading="Sayfalar">
                  {results.pages.map((item) => (
                    <CommandItem 
                      key={`page-${item.id}`}
                      onSelect={() => handleSelect(item, 'page')}
                    >
                      <File className="mr-2 h-4 w-4" />
                      <span>{item.title}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              
              {/* Servers */}
              {results.servers.length > 0 && (
                <CommandGroup heading="Sunucular">
                  {results.servers.map((item) => (
                    <CommandItem 
                      key={`server-${item.id}`}
                      onSelect={() => handleSelect(item, 'server')}
                    >
                      <Server className="mr-2 h-4 w-4" />
                      <span>{item.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              
              {/* Users */}
              {results.users.length > 0 && (
                <CommandGroup heading="Kullanıcılar">
                  {results.users.map((item) => (
                    <CommandItem 
                      key={`user-${item.id}`}
                      onSelect={() => handleSelect(item, 'user')}
                    >
                      <Users className="mr-2 h-4 w-4" />
                      <span>{item.name}</span>
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                        {item.role}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              
              {/* Docs */}
              {results.docs.length > 0 && (
                <CommandGroup heading="Dokümanlar">
                  {results.docs.map((item) => (
                    <CommandItem 
                      key={`doc-${item.id}`}
                      onSelect={() => handleSelect(item, 'doc')}
                    >
                      <File className="mr-2 h-4 w-4" />
                      <div className="overflow-hidden text-ellipsis">
                        <span>{item.title}</span>
                        <span className="text-xs text-muted-foreground ml-2">
                          {item.category}
                        </span>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              
              {/* No results */}
              {results.queries.length === 0 && 
               results.pages.length === 0 && 
               results.servers.length === 0 && 
               results.users.length === 0 && 
               results.docs.length === 0 && (
                <CommandEmpty>
                  Sonuç bulunamadı.
                </CommandEmpty>
              )}
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss

export default SearchBox;