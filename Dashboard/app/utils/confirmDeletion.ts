import Swal from 'sweetalert2';
import 'sweetalert2/dist/sweetalert2.min.css';

interface ConfirmDeletionOptions {
  title?: string;
  text: string;
  confirmButtonText?: string;
}

export async function confirmDeletion({
  title = 'Are you sure?',
  text,
  confirmButtonText = 'Yes, delete it',
}: ConfirmDeletionOptions): Promise<boolean> {
  const result = await Swal.fire({
    title,
    text,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText,
    cancelButtonText: 'Cancel',
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#393f56',
    background: '#1b1d28',
    color: '#ffffff',
    reverseButtons: true,
    focusCancel: true,
  });

  return result.isConfirmed;
}
