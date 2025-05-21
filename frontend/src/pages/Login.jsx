import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { AlertCircle, Lock, User } from 'lucide-react';
import { login } from '@/api/auth';
import { setAuthToken } from '@/utils/auth';

const LoginPage = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      username: 'Teeksss',
      password: '••••••••'
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const currentDateTime = new Date('2025-05-16 13:26:53');
  
  const onSubmit = async (data) => {
    setIsLoading(true);
    try {
      // Simulate API call for demo
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock response
      const response = {
        access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJUZWVrc3NzIiwicm9sZSI6ImFkbWluIiwiZW1haWwiOiJ0ZWVrc3NzQGV4YW1wbGUuY29tIiwiZXhwIjoxNzM3NDMzNjEzfQ.signature",
        expires_at: Math.floor(new Date('2025-05-16 17:26:53').getTime() / 1000),
        user: {
          username: 'Teeksss',
          displayName: 'Teeksss',
          role: 'admin',
          email: 'teeksss@example.com'
        }
      };
      
      // Store auth token and user info
      setAuthToken(
        response.access_token, 
        response.expires_at, 
        response.user
      );
      
      toast({
        title: "Giriş Başarılı",
        description: `Hoş geldiniz, ${response.user.displayName}! Yönlendiriliyorsunuz...`,
        variant: "default",
      });
      
      // Redirect based on role
      if (response.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
      
    } catch (error) {
      console.error('Login error:', error);
      
      toast({
        title: "Giriş Başarısız",
        description: error.message || "Kullanıcı adı veya şifre hatalı.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <div className="w-full max-w-md p-4">
        <Card>
          <CardHeader className="space-y-1">
            <div className="flex justify-center mb-4">
              <div className="p-2 bg-blue-100 rounded-full">
                <Lock className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <CardTitle className="text-2xl text-center">
              SQL Proxy Giriş
            </CardTitle>
            <CardDescription className="text-center">
              Kimlik bilgilerinizle giriş yapın
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">
                    Kullanıcı Adı
                  </Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                      <User className="h-5 w-5 text-gray-400" />
                    </div>
                    <Input
                      id="username"
                      type="text"
                      className="pl-10"
                      placeholder="LDAP kullanıcı adınız"
                      {...register("username", { 
                        required: "Kullanıcı adı gerekli" 
                      })}
                    />
                  </div>
                  {errors.username && (
                    <p className="text-sm text-red-500 flex items-center mt-1">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {errors.username.message}
                    </p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">
                    Şifre
                  </Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                      <Lock className="h-5 w-5 text-gray-400" />
                    </div>
                    <Input
                      id="password"
                      type="password"
                      className="pl-10"
                      placeholder="LDAP şifreniz"
                      {...register("password", { 
                        required: "Şifre gerekli" 
                      })}
                    />
                  </div>
                  {errors.password && (
                    <p className="text-sm text-red-500 flex items-center mt-1">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {errors.password.message}
                    </p>
                  )}
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                      Giriş yapılıyor...
                    </>
                  ) : (
                    "Giriş Yap"
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col text-xs text-center text-gray-500">
            <div>
              Bu sistem LDAP kimlik doğrulaması kullanmaktadır. 
              Şirket kullanıcı adınız ve şifrenizi kullanın.
            </div>
            <div className="mt-2 text-gray-400">
              {currentDateTime.toLocaleString()} • Sistem Sürümü v1.0.1
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;