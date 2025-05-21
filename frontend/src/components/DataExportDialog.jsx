import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/components/ui/use-toast';
import { Download, FileSpreadsheet, FileText, Database, LoaderIcon } from 'lucide-react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Define form schema
const exportFormSchema = z.object({
  format: z.enum(['csv', 'excel', 'json', 'parquet'], {
    required_error: 'Lütfen bir dışa aktarma formatı seçin',
  }),
  includeHeaders: z.boolean().default(true),
  limitRows: z.boolean().default(false),
});

/**
 * Dialog component for exporting data to different formats
 * 
 * @param {Object} props Component props
 * @param {Function} props.onExport Callback when export is confirmed
 * @param {boolean} props.disabled Whether the export button is disabled
 * @param {string} props.label Label for the trigger button
 * @param {React.ReactNode} props.triggerElement Custom trigger element
 * @param {number} props.rowCount Number of rows in the data
 * @returns {JSX.Element} Data export dialog component
 */
const DataExportDialog = ({ 
  onExport, 
  disabled = false, 
  label = "Dışa Aktar", 
  triggerElement = null, 
  rowCount = 0
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  
  // Initialize form
  const form = useForm({
    resolver: zodResolver(exportFormSchema),
    defaultValues: {
      format: 'csv',
      includeHeaders: true,
      limitRows: false,
    },
  });
  
  // Handle form submission
  const onSubmit = async (values) => {
    if (loading) return;
    
    setLoading(true);
    try {
      await onExport(values);
      setOpen(false);
      toast({
        title: "Dışa aktarma başarılı",
        description: `Veriler ${values.format.toUpperCase()} formatında dışa aktarıldı.`,
        duration: 3000,
      });
    } catch (error) {
      console.error('Export error:', error);
      toast({
        title: "Dışa aktarma hatası",
        description: error.message || "Veriler dışa aktarılırken bir hata oluştu.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const formatIcons = {
    csv: <FileText className="h-4 w-4 mr-2" />,
    excel: <FileSpreadsheet className="h-4 w-4 mr-2" />,
    json: <Database className="h-4 w-4 mr-2" />,
    parquet: <Database className="h-4 w-4 mr-2" />,
  };
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {triggerElement || (
          <Button disabled={disabled} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            {label}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Veri Dışa Aktarma</DialogTitle>
          <DialogDescription>
            Verileri farklı formatlarda dışa aktarabilirsiniz. ({rowCount} satır)
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="format"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>Dosya Formatı</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      className="grid grid-cols-2 gap-4"
                    >
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="csv" />
                        </FormControl>
                        <FormLabel className="font-normal flex items-center cursor-pointer">
                          {formatIcons.csv} CSV
                        </FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="excel" />
                        </FormControl>
                        <FormLabel className="font-normal flex items-center cursor-pointer">
                          {formatIcons.excel} Excel
                        </FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="json" />
                        </FormControl>
                        <FormLabel className="font-normal flex items-center cursor-pointer">
                          {formatIcons.json} JSON
                        </FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="parquet" />
                        </FormControl>
                        <FormLabel className="font-normal flex items-center cursor-pointer">
                          {formatIcons.parquet} Parquet
                        </FormLabel>
                      </FormItem>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <div className="flex flex-col gap-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeHeaders"
                  checked={form.watch('includeHeaders')}
                  onCheckedChange={(checked) => form.setValue('includeHeaders', checked)}
                />
                <label
                  htmlFor="includeHeaders"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  Başlık satırı ekle
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="limitRows"
                  checked={form.watch('limitRows')}
                  onCheckedChange={(checked) => form.setValue('limitRows', checked)}
                />
                <label
                  htmlFor="limitRows"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  İlk 1000 satırla sınırla (büyük veri kümeleri için önerilir)
                </label>
              </div>
            </div>
            
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={loading}
              >
                İptal
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <LoaderIcon className="h-4 w-4 mr-2 animate-spin" />
                    İşleniyor...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Dışa Aktar
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

// Son güncelleme: 2025-05-20 10:00:16
// Güncelleyen: Teeksss

export default DataExportDialog;