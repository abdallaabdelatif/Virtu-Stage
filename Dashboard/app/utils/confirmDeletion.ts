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
    cancelButtonColor: '#46513c',
    background: '#1a2117',
    color: '#ffffff',
    reverseButtons: true,
    focusCancel: true,
  });

  return result.isConfirmed;
}
